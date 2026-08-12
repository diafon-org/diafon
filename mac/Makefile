# Diaphone input method — build/install without Xcode (Command Line Tools are enough).
#   make check     validate the Swift engine port against the Python CLI (480 cases)
#   make app       build build/DiaphoneIM.app (ad-hoc signed)
#   make install   copy to ~/Library/Input Methods and restart it
ROOT  := ..
BUILD := build
APP   := DiaphoneIM
SWIFTC := xcrun swiftc -swift-version 5 -O
CORE  := Sources/Engine.swift Sources/Decoder.swift Sources/Streamer.swift
APPSRC := Sources/main.swift Sources/Config.swift Sources/DiaphoneInputController.swift

.PHONY: engine check app install clean

engine:
	@mkdir -p $(BUILD)
	cd $(ROOT) && PYTHONPATH=src python3 -m diaphone.cli export-json --out mac/$(BUILD)/engine.json

$(BUILD)/diaphone-check: $(CORE) Sources/CheckMain.swift
	@mkdir -p $(BUILD)
	$(SWIFTC) $(CORE) Sources/CheckMain.swift -o $@

check: engine $(BUILD)/diaphone-check
	cd $(ROOT) && PYTHONPATH=src python3 scripts/check_swift.py mac/$(BUILD)/diaphone-check mac/$(BUILD)/engine.json

app: engine check
	@mkdir -p $(BUILD)/$(APP).app/Contents/MacOS
	@mkdir -p $(BUILD)/$(APP).app/Contents/Resources
	$(SWIFTC) $(CORE) $(APPSRC) -framework Cocoa -framework InputMethodKit \
		-o $(BUILD)/$(APP).app/Contents/MacOS/$(APP)
	cp Info.plist $(BUILD)/$(APP).app/Contents/Info.plist
	cp $(BUILD)/engine.json $(BUILD)/$(APP).app/Contents/Resources/engine.json
	codesign --force --sign - $(BUILD)/$(APP).app

install: app
	rm -rf "$$HOME/Library/Input Methods/$(APP).app"
	cp -R $(BUILD)/$(APP).app "$$HOME/Library/Input Methods/"
	-pkill -x $(APP) 2>/dev/null || true
	@echo ""
	@echo "Installed. Enable it: System Settings → Keyboard → Input Sources → Edit… → + →"
	@echo "search “Diaphone” (under English). Then pick it from the input menu and type."

clean:
	rm -rf $(BUILD)
