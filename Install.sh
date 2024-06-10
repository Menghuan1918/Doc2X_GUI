#!/bin/bash

current_dir=$(pwd)
desktop_file="Doc2X GUI.desktop"
desktop_path="$HOME/.local/share/applications"
app_name="Doc2X GUI"

install() {
    echo "[Desktop Entry]" > "$desktop_path/$desktop_file"
    echo "Name=$app_name" >> "$desktop_path/$desktop_file"
    echo "Comment=Doc2X third party desktop client Application" >> "$desktop_path/$desktop_file"
    echo "Exec=sh -c 'cd $current_dir && ./Doc2X.bin'" >> "$desktop_path/$desktop_file"
    echo "Icon=$current_dir/icon.png" >> "$desktop_path/$desktop_file"
    echo "Terminal=false" >> "$desktop_path/$desktop_file"
    echo "Type=Application" >> "$desktop_path/$desktop_file"
    echo "Categories=Utility;" >> "$desktop_path/$desktop_file"

    update-desktop-database "$desktop_path"

    echo "Install $app_name done!"
}

uninstall() {
    rm "$desktop_path/$desktop_file"

    update-desktop-database "$desktop_path"

    echo "Uninstall $app_name done, you also need to delete the directory manually!"
}

main() {
    if [ "$1" == "install" ]; then
        install
    elif [ "$1" == "uninstall" ]; then
        uninstall
    elif [ "$1" == "help" ]; then
        echo "Useage:
-Install: sh $0 install
-Uninstall: sh $0 uninstall"
    else
        install
    fi
}

main "$1"