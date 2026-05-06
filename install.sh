#!/usr/bin/env bash
# =============================================================================
#  Flatlink Installer — Poniek Labs
#  Installs Flatlink system-wide and sets up Flatpak + Flathub if needed.
# =============================================================================

set -euo pipefail

APP_NAME="flatlink"
INSTALL_DIR="/usr/local/lib/flatlink"
BIN_LINK="/usr/local/bin/flatlink"
DESKTOP_FILE="/usr/share/applications/flatlink.desktop"
ICON_DIR="/usr/share/icons/hicolor/128x128/apps"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; exit 1; }

# ── Root check ────────────────────────────────────────────────────────────────
if [[ "$EUID" -ne 0 ]]; then
    error "This installer must be run as root.\n       Re-run with: sudo bash install.sh"
fi

echo -e "\n${BOLD}╔══════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║         Flatlink Installer v1.0          ║${RESET}"
echo -e "${BOLD}║         Poniek Labs                      ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${RESET}\n"

# ── Detect package manager ───────────────────────────────────────────────────
detect_pkg_manager() {
    if   command -v apt-get  &>/dev/null; then echo "apt"
    elif command -v dnf      &>/dev/null; then echo "dnf"
    elif command -v yum      &>/dev/null; then echo "yum"
    elif command -v pacman   &>/dev/null; then echo "pacman"
    elif command -v zypper   &>/dev/null; then echo "zypper"
    else error "No supported package manager found (apt/dnf/yum/pacman/zypper)."; fi
}

PKG_MGR="$(detect_pkg_manager)"
info "Detected package manager: ${BOLD}${PKG_MGR}${RESET}"

# ── Install a package via detected manager ───────────────────────────────────
pkg_install() {
    local pkg="$1"
    info "Installing ${BOLD}${pkg}${RESET} …"
    case "$PKG_MGR" in
        apt)    apt-get install -y "$pkg" ;;
        dnf)    dnf install -y "$pkg" ;;
        yum)    yum install -y "$pkg" ;;
        pacman) pacman -S --noconfirm "$pkg" ;;
        zypper) zypper install -y "$pkg" ;;
    esac
}

# ── 1. Python 3 ───────────────────────────────────────────────────────────────
info "Checking for Python 3 …"
if ! command -v python3 &>/dev/null; then
    pkg_install python3
else
    PY_VER="$(python3 --version 2>&1)"
    success "Found ${PY_VER}"
fi

# ── 2. tkinter ───────────────────────────────────────────────────────────────
info "Checking for tkinter …"
if ! python3 -c "import tkinter" &>/dev/null; then
    warn "tkinter not found — installing …"
    case "$PKG_MGR" in
        apt)    pkg_install python3-tk ;;
        dnf|yum) pkg_install python3-tkinter ;;
        pacman) pkg_install tk ;;
        zypper) pkg_install python3-tk ;;
    esac
else
    success "tkinter is available"
fi

# ── 3. Flatpak ───────────────────────────────────────────────────────────────
info "Checking for Flatpak …"
if ! command -v flatpak &>/dev/null; then
    warn "Flatpak not found — installing …"
    pkg_install flatpak
    success "Flatpak installed"
else
    FLAT_VER="$(flatpak --version 2>&1)"
    success "Found ${FLAT_VER}"
fi

# ── 4. Flathub remote ────────────────────────────────────────────────────────
info "Checking for Flathub remote …"
if flatpak remotes --system 2>/dev/null | grep -q "^flathub"; then
    success "Flathub remote already configured (system)"
else
    info "Adding Flathub remote (system-wide) …"
    flatpak remote-add --if-not-exists --system flathub \
        https://dl.flathub.org/repo/flathub.flatpakrepo
    success "Flathub remote added"
fi

# ── 5. Copy application files ────────────────────────────────────────────────
info "Installing Flatlink to ${INSTALL_DIR} …"
mkdir -p "$INSTALL_DIR"

# Locate the main Python script (same dir as this installer, or current dir)
MAIN_PY=""
for candidate in "${SCRIPT_DIR}/flatlink.py" "${SCRIPT_DIR}/main.py" "$(pwd)/flatlink.py" "$(pwd)/main.py"; do
    if [[ -f "$candidate" ]]; then
        MAIN_PY="$candidate"
        break
    fi
done

if [[ -z "$MAIN_PY" ]]; then
    error "Could not find flatlink.py / main.py next to the installer.\n       Make sure install.sh and the Python source are in the same directory."
fi

cp "$MAIN_PY" "${INSTALL_DIR}/flatlink.py"
chmod 644 "${INSTALL_DIR}/flatlink.py"
success "Copied $(basename "$MAIN_PY") → ${INSTALL_DIR}/flatlink.py"

# Copy any extra assets that exist alongside the installer
for asset in icon.png flatlink.png; do
    src="${SCRIPT_DIR}/${asset}"
    if [[ -f "$src" ]]; then
        mkdir -p "$ICON_DIR"
        cp "$src" "${ICON_DIR}/flatlink.png"
        success "Installed icon → ${ICON_DIR}/flatlink.png"
        break
    fi
done

# ── 6. Launcher script in PATH ───────────────────────────────────────────────
info "Creating launcher at ${BIN_LINK} …"
cat > "$BIN_LINK" <<'EOF'
#!/usr/bin/env bash
exec python3 /usr/local/lib/flatlink/flatlink.py "$@"
EOF
chmod 755 "$BIN_LINK"
success "Launcher created — run ${BOLD}flatlink${RESET} from any terminal"

# ── 7. .desktop entry ────────────────────────────────────────────────────────
info "Installing .desktop entry …"

# Resolve icon: use installed one if available, fall back to a themed name
if [[ -f "${ICON_DIR}/flatlink.png" ]]; then
    ICON_VALUE="${ICON_DIR}/flatlink.png"
else
    ICON_VALUE="package-x-generic"
fi

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Flatlink
GenericName=Flathub App Installer
Comment=Install Flatpak apps from Flathub by pasting a link
Exec=flatlink
Icon=${ICON_VALUE}
Terminal=false
Categories=System;PackageManager;
Keywords=flatpak;flathub;install;app;
StartupNotify=true
EOF

chmod 644 "$DESKTOP_FILE"

# Refresh icon + desktop caches if available
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database /usr/share/applications &>/dev/null || true
fi
if command -v gtk-update-icon-cache &>/dev/null && [[ -d /usr/share/icons/hicolor ]]; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor &>/dev/null || true
fi

success ".desktop entry installed → ${DESKTOP_FILE}"

# ── Done ─────────────────────────────────────────────────────────────────────
echo
echo -e "${GREEN}${BOLD}✔  Flatlink installed successfully!${RESET}"
echo -e "   • Run from terminal : ${BOLD}flatlink${RESET}"
echo -e "   • Or find ${BOLD}Flatlink${RESET} in your application menu / launcher"
echo
