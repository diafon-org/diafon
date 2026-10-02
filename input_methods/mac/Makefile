# Diafon input method for macOS — build/install without Xcode (Command Line Tools are enough).
#   make data      regenerate Sources/SpecData.swift from docs/spec.json
#   make check     replay the spec vectors through the Swift engine (tests/test_swift.py)
#   make app       build build/DiafonIM.app (ad-hoc signed)
#   make install   copy to ~/Library/Input Methods and restart it
#   make enable    enable the input source and select it (disables the old Diaphone one)
ROOT  := ../..
BUILD := build
APP   := DiafonIM
SWIFTC := xcrun swiftc -swift-version 5 -O
CORE  := Sources/SpecData.swift Sources/Engine.swift Sources/Stages.swift Sources/Reading.swift Sources/Lexicon.swift
APPSRC := Sources/main.swift Sources/Prefs.swift Sources/Services.swift Sources/ConvertWindow.swift Sources/Hud.swift Sources/LanguageChooser.swift Sources/SetupWindow.swift Sources/DiafonInputController.swift

.PHONY: data check app install enable clean

data:
	cd $(ROOT) && python3 scripts/gen_mac.py

check:
	cd $(ROOT) && python3 tests/test_swift.py

app: check
	@mkdir -p $(BUILD)/$(APP).app/Contents/MacOS $(BUILD)/$(APP).app/Contents/Resources
	$(SWIFTC) $(CORE) $(APPSRC) -framework Cocoa -framework InputMethodKit \
		-o $(BUILD)/$(APP).app/Contents/MacOS/$(APP)
	cp Info.plist $(BUILD)/$(APP).app/Contents/Info.plist
	cp $(ROOT)/docs/logo/Diafon.icns $(BUILD)/$(APP).app/Contents/Resources/Diafon.icns
	cp $(ROOT)/docs/logo/DiafonMenu.tiff $(BUILD)/$(APP).app/Contents/Resources/DiafonMenu.tiff
	mkdir -p $(BUILD)/$(APP).app/Contents/Resources/lexicon && cp $(ROOT)/data/lexicon/*.json $(BUILD)/$(APP).app/Contents/Resources/lexicon/
	codesign --force --sign - $(BUILD)/$(APP).app

install: app
	rm -rf "$$HOME/Library/Input Methods/$(APP).app" "$$HOME/Library/Input Methods/DiaphoneIM.app"
	cp -R $(BUILD)/$(APP).app "$$HOME/Library/Input Methods/"
	-pkill -x $(APP) 2>/dev/null || true
	-/System/Library/CoreServices/pbs -update 2>/dev/null
	-/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -u $(BUILD)/$(APP).app 2>/dev/null
	-/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$$HOME/Library/Input Methods/$(APP).app" 2>/dev/null
	@echo ""
	@echo "Installed. Enable it once: System Settings → Keyboard → Input Sources → Edit… → + →"
	@echo "search “Diafon” (under English). Pick it from the input menu and type: sjok sewp njawr → șok sép ņár."

enable:
	swift tools/enable.swift

clean:
	rm -rf $(BUILD)
