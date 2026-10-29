# Diafon keyboard for iOS. Needs Xcode (the iOS SDK) and XcodeGen for the
# project and builds; `make check` needs only the Command Line Tools.
#   make check     the keystroke logic and the spec vectors on the Mac, and a
#                  UIKit typecheck through Mac Catalyst (tests/test_ios_session.py)
#   make data      regenerate the shared tables (SpecData.swift, Layouts.swift)
#   make project   write Diafon.xcodeproj from project.yml (TEAM=<team id> to sign)
#   make sim       build for the simulator
#   make uitest    type on the keyboard in a simulator (UITests/KeyboardTests.swift); SIM=<device name>
#   make open      open the project in Xcode (run on a device from there)
ROOT  := ../..
TEAM  ?=
SIM   ?= iPhone 17
ICON  := App/Assets.xcassets/AppIcon.appiconset/icon-1024.png

.PHONY: check data icon project sim uitest open clean

check:
	cd $(ROOT) && python3 tests/test_swift.py && python3 tests/test_ios_session.py

data:
	cd $(ROOT) && python3 scripts/gen_mac.py && python3 scripts/gen_layouts.py

# the icon is the site's, made by fonts/tools/logo.py; copied, not kept twice in git
icon:
	cp $(ROOT)/docs/logo/png/icon-1024.png $(ICON)

project: icon
	xcodegen generate
	@if [ -n "$(TEAM)" ]; then sed -i '' 's/DEVELOPMENT_TEAM = "";/DEVELOPMENT_TEAM = $(TEAM);/' Diafon.xcodeproj/project.pbxproj; fi

sim: check project
	xcodebuild -project Diafon.xcodeproj -scheme Diafon -destination 'generic/platform=iOS Simulator' -derivedDataPath build -quiet build

# the keyboard must be on the simulator's list; the defaults write puts it there
uitest: check project
	xcrun simctl boot '$(SIM)' 2>/dev/null || true
	xcrun simctl spawn '$(SIM)' defaults write .GlobalPreferences AppleKeyboards -array 'en_US@sw=QWERTY;hw=Automatic' 'io.diafon.app.keyboard' 'emoji@sw=Emoji'
	defaults write com.apple.iphonesimulator ConnectHardwareKeyboard -bool false
	rm -rf build/ui.xcresult
	xcodebuild -project Diafon.xcodeproj -scheme Diafon -destination 'platform=iOS Simulator,name=$(SIM)' -derivedDataPath build -resultBundlePath build/ui.xcresult test

open: project
	open Diafon.xcodeproj

clean:
	rm -rf Diafon.xcodeproj build $(ICON)
