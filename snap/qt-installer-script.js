// This script is here for convenience. Minify it and copy it into the
// qt5 override-build section of snapcraft.yaml

function Controller() {
    installer.installationFinished.connect(proceed)
}

function logCurrentPage() {
    var pageName = page().objectName
    var pagePrettyTitle = page().title
    console.log('At page: ' + pageName + ' (' + pagePrettyTitle + ')')
}

function page() {
    return gui.currentPageWidget()
}

function proceed(button, delay) {
    gui.clickButton(button || buttons.NextButton, delay)
}

Controller.prototype.WelcomePageCallback = function () {
    logCurrentPage()
    proceed(buttons.NextButton, 2000)
}

Controller.prototype.CredentialsPageCallback = function () {
    logCurrentPage()
    proceed()
}

Controller.prototype.IntroductionPageCallback = function () {
    logCurrentPage()
    proceed()
}

Controller.prototype.TargetDirectoryPageCallback = function () {
    logCurrentPage()
    var dir = installer.environmentVariable('SNAPCRAFT_PART_INSTALL') + '/opt/Qt5.14.0'
    console.log('Installing to ' + dir)
    page().TargetDirectoryLineEdit.setText(dir)
    proceed()
}

Controller.prototype.ComponentSelectionPageCallback = function () {
    logCurrentPage()
    page().deselectAll()
    page().selectComponent('qt.qt5.5140.gcc_64')
    proceed()
}

Controller.prototype.LicenseAgreementPageCallback = function () {
    logCurrentPage()
    page().AcceptLicenseRadioButton.checked = true
    gui.clickButton(buttons.NextButton)
}

Controller.prototype.ReadyForInstallationPageCallback = function () {
    logCurrentPage()
    proceed()
}

Controller.prototype.PerformInstallationPageCallback = function () {
    logCurrentPage()
}

Controller.prototype.FinishedPageCallback = function () {
    logCurrentPage()
    proceed(buttons.FinishButton)
}

Controller.prototype.DynamicTelemetryPluginFormCallback = function () {
    logCurrentPage()
    console.log(Object.keys(page().TelemetryPluginForm.statisticGroupBox))
    var radioButtons = page().TelemetryPluginForm.statisticGroupBox
    radioButtons.disableStatisticRadioButton.checked = true
    proceed()
}