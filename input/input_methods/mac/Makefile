# Diafon input method for macOS — build/install without Xcode (Command Line Tools are enough).
#   make data      the alphabet and the typing the app bundles (../apple/Resources, scripts/gen_apple.py)
#   make check     replay the vectors through the shared core (tests/test_apple.py)
#   make app       build build/DiafonIM.app (ad-hoc signed)
#   make install   copy to ~/Library/Input Methods and restart it
#   make enable    enable the input source and select it (disables the old Diaphone one)
ROOT  := ../..
BUILD := build
APP   := DiafonIM
SWIFTC := xcrun swiftc -swift-version 5 -O
CORE  := $(ROOT)/input_methods/apple/Core/Diafon.swift $(ROOT)/input_methods/apple/Core/Prefs.swift $(ROOT)/input_methods/apple/Core/Layouts.swift
RES   := $(ROOT)/input_methods/apple/Resources
APPSRC := Sources/MacPrefs.swift Sources/Keyboards.swift Sources/main.swift Sources/Services.swift Sources/ConvertWindow.swift Sources/Hud.swift Sources/LanguageChooser.swift Sources/SetupWindow.swift Sources/DiafonInputController.swift

.PHONY: data check app install enable clean

data:
	cd $(ROOT) && python3 scripts/gen_apple.py

check:
	cd $(ROOT) && python3 tests/test_apple.py

app: check
	@mkdir -p $(BUILD)/$(APP).app/Contents/MacOS $(BUILD)/$(APP).app/Contents/Resources
	$(SWIFTC) $(CORE) $(APPSRC) -framework Cocoa -framework InputMethodKit -framework JavaScriptCore \
		-o $(BUILD)/$(APP).app/Contents/MacOS/$(APP)
	cp $(RES)/alphabet.json $(RES)/typing.json $(RES)/lexicons.json $(RES)/diafon-core.js $(RES)/diafon-keys.js $(RES)/diafon-glue.js $(BUILD)/$(APP).app/Contents/Resources/
	python3 tools/modes.py Info.plist $(BUILD)/$(APP).app/Contents      # Info.plist with one input mode per output
	cp $(ROOT)/../docs/logo/Diafon.icns $(BUILD)/$(APP).app/Contents/Resources/Diafon.icns
	cp $(ROOT)/../docs/logo/DiafonMenu.tiff $(BUILD)/$(APP).app/Contents/Resources/DiafonMenu.tiff
	cp $(ROOT)/../docs/logo/DiafonBadge.pdf $(BUILD)/$(APP).app/Contents/Resources/DiafonBadge.pdf
	mkdir -p $(BUILD)/$(APP).app/Contents/Resources/Fonts && cp $(ROOT)/../fonts/Diafon*-Regular.ttf $(BUILD)/$(APP).app/Contents/Resources/Fonts/
	codesign --force --sign - $(BUILD)/$(APP).app

install: clean app
	rm -rf "$$HOME/Library/Input Methods/$(APP).app" "$$HOME/Library/Input Methods/DiaphoneIM.app"
	cp -R $(BUILD)/$(APP).app "$$HOME/Library/Input Methods/"
	-pkill -x $(APP) 2>/dev/null || true
	-/System/Library/CoreServices/pbs -update 2>/dev/null
	-/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -u $(BUILD)/$(APP).app 2>/dev/null
	-/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$$HOME/Library/Input Methods/$(APP).app" 2>/dev/null
	@echo ""
	@echo "Installed. Enable it once: System Settings → Keyboard → Input Sources → Edit… → + →"
	@echo "search “Diafon” (under English). Pick it from the input menu and type: sy cy aq → ș c̦ á."

enable:
	swift tools/enable.swift

clean:
	rm -rf $(BUILD)
