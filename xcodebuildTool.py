#!/usr/bin/env python
# -*- coding:utf-8 -*-

# 需要安装xcpretty, 使用Python 2.7版本运行

import argparse
import subprocess
import requests
import os
import datetime

# ============== 必 填 项 ==============
# 配置打包TARGET
TARGET = 'LanSynergism'
# 配置打包类型
CONFIGURATION = "Debug"
# 配置打包版本
VERSION = '1.1.0'
BUILD = '10'
# 上传app store
UPLOAD_TO_APPSTORE = False
# 上传蒲公英
UPLOAD_TO_PGY = True
# 删除Archive文件
DELETE_ARCHIVE_FILE = False
# 是否需要pod install
POD_INSTALL = True

# 配置导出archive选项
EXPORT_OPTIONS_PLIST = "exportOptions.plist"
# Info.plist路径(运行时会替换info.plist文件中的版本号)
PLIST_PATH = "~/Desktop/Workspace/LanSynergism/LanSynergism/LanSynergism/Info.plist"

# ============== 可 选 项 ==============
# 输出文件根目录
DATE = datetime.datetime.now().strftime('%m-%d-%H-%M')
EXPORT_MAIN_DIRECTORY = "~/Desktop/%s" % TARGET
# xcarchive文件路径(含有dsym)
ARCHIVEPATH = EXPORT_MAIN_DIRECTORY + "/%s_%s.xcarchive" % (TARGET, VERSION)
# ipa路径
IPAPATH = EXPORT_MAIN_DIRECTORY + "/%s%s.ipa" % (TARGET, VERSION)

# ============== 导出AppStore选项 ==============
# 苹果开发者账号
APPLEID = 'APPLEID'
APPLEPWD = 'APPLEPWD'

# ============== 上传至蒲公英选项 ==============
PGYER_UPLOAD_URL = "http://www.pgyer.com/apiv1/app/upload"
DOWNLOAD_BASE_URL = "http://www.pgyer.com"
USER_KEY = "d9f8ff6ca7630e22d15eb55c6cfd2"
API_KEY = "ddb5011563b5b3becc556407d48c7"
# 设置从蒲公英下载应用时的密码(默认无)
PYGER_PASSWORD = ""

# 清理目标文件夹
def cleanArchiveFile():
    cleanCmd = "rm -r %s" % ARCHIVEPATH
    process = subprocess.Popen(cleanCmd, shell=True)
    process.wait()
    print "-> Cleaned archiveFile: %s" % ARCHIVEPATH


# Pod install
def executePodInstall():
    print "-> Pod install......"
    podInstallCmd = "pod install"
    process = subprocess.Popen(podInstallCmd, shell=True)
    process.wait()
    podRetureCode = process.returncode
    if podRetureCode != 0:
        print "-> Pod install failed!"


# 打包Project文件
def buildProject(project):
    print "打包Project文件!"
    archiveCmd = 'xcodebuild -project %s -scheme %s -configuration %s archive -archivePath %s -destination generic/platform=iOS' % (
    project, TARGET, CONFIGURATION, ARCHIVEPATH)
    process = subprocess.Popen(archiveCmd, shell=True)
    process.wait()

    archiveReturnCode = process.returncode
    if archiveReturnCode != 0:
        print "archive project %s failed" % project
        cleanArchiveFile()


# 打包workspace文件
def buildWorkspace(workspace):
    print "打包workspace文件!"
    archiveCmd = 'xcodebuild -workspace %s -scheme %s -configuration %s archive -archivePath %s -destination generic/platform=iOS | xcpretty' % (
    workspace, TARGET, CONFIGURATION, ARCHIVEPATH)
    process = subprocess.Popen(archiveCmd, shell=True)
    process.wait()

    archiveReturnCode = process.returncode
    if archiveReturnCode != 0:
        print "archive workspace %s failed" % workspace
        cleanArchiveFile()


# 导出IPA文件
def exportArchive():
    exportCmd = "xcodebuild -exportArchive -archivePath %s -exportPath %s -exportOptionsPlist %s" % (
        ARCHIVEPATH, EXPORT_MAIN_DIRECTORY, EXPORT_OPTIONS_PLIST)
    process = subprocess.Popen(exportCmd, shell=True)
    (stdoutdata, stderrdata) = process.communicate()

    signReturnCode = process.returncode
    if signReturnCode != 0:
        print "export %s failed" % TARGET
        return ""
    else:
        return EXPORT_MAIN_DIRECTORY


# 上传App Store
def uploadIpaToAppStore():
    print "iPA上传中...."
    altoolPath = "/Applications/Xcode.app/Contents/Applications/Application\ Loader.app/Contents/Frameworks/ITunesSoftwareService.framework/Versions/A/Support/altool"

    exportCmd = "%s --validate-app -f %s -u %s -p %s -t ios --output-format xml" % (
    altoolPath, IPAPATH, APPLEID, APPLEPWD)
    process = subprocess.Popen(exportCmd, shell=True)
    (stdoutdata, stderrdata) = process.communicate()

    validateResult = process.returncode
    if validateResult == 0:
        print '~~~~~~~~~~~~~~~~iPA验证通过~~~~~~~~~~~~~~~~'
        exportCmd = "%s --upload-app -f %s -u %s -p %s -t ios --output-format normal" % (
            altoolPath, IPAPATH, APPLEID, APPLEPWD)
        process = subprocess.Popen(exportCmd, shell=True)
        (stdoutdata, stderrdata) = process.communicate()

        uploadresult = process.returncode
        if uploadresult == 0:
            print '~~~~~~~~~~~~~~~~iPA上传成功'
        else:
            print '~~~~~~~~~~~~~~~~iPA上传失败'
    else:
        print "~~~~~~~~~~~~~~~~iPA验证失败~~~~~~~~~~~~~~~~"


# 上传蒲公英
def uploadIpaToPgyer(ipaPath):
    print "ipaPath:" + ipaPath
    ipaPath = os.path.expanduser(ipaPath)
    ipaPath = unicode(ipaPath, "utf-8")
    files = {'file': open(ipaPath, 'rb')}
    headers = {'enctype': 'multipart/form-data'}
    payload = {'uKey': USER_KEY, '_api_key': API_KEY, 'publishRange': '2', 'isPublishToPublic': '2',
               'password': PYGER_PASSWORD}
    print "uploading...."
    r = requests.post(PGYER_UPLOAD_URL, data=payload, files=files, headers=headers)
    if r.status_code == requests.codes.ok:
        result = r.json()
        parserUploadResult(result)
    else:
        print 'HTTPError,Code:' + r.status_code


# 解析蒲公英返回参数
def parserUploadResult(jsonResult):
    resultCode = jsonResult['code']
    if resultCode == 0:
        downUrl = DOWNLOAD_BASE_URL + "/" + jsonResult['data']['appShortcutUrl']
        print("Upload Success")
        print("DownUrl is:" + downUrl)
    else:
        print "Upload Fail!"
        print "Reason:" + jsonResult['message']


# 执行打包
def xcbuild(options):
    project = options.project
    workspace = options.workspace

    if project is None and workspace is None:
        pass
    elif project is not None:
        buildProject(project)
        print "-> Project is not none!"
    elif workspace is not None:
        print "-> workspace is not none!"
        if POD_INSTALL:
            executePodInstall()
        buildWorkspace(workspace)

    # 导出ipa文件
    exportarchive = exportArchive()
    if UPLOAD_TO_PGY and exportarchive != "":
        uploadIpaToPgyer(IPAPATH)

    if UPLOAD_TO_APPSTORE:
        uploadIpaToAppStore()
    else:
        if DELETE_ARCHIVE_FILE:
            cleanArchiveFile()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--workspace", help="Build the workspace name.xcworkspace.", metavar="name.xcworkspace")
    parser.add_argument("-p", "--project", help="Build the project name.xcodeproj.", metavar="name.xcodeproj")

    options = parser.parse_args()

    print ("options: %s" % options)

    os.system('/usr/libexec/PlistBuddy -c "Set:CFBundleShortVersionString %s" %s' % (VERSION, PLIST_PATH))
    os.system('/usr/libexec/PlistBuddy -c "Set:CFBundleVersion %s" %s' % (BUILD, PLIST_PATH))

    xcbuild(options)


if __name__ == '__main__':
    main()
