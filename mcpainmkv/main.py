#!/usr/bin/env python3
import argparse
import importlib.util
import os
from pathlib import Path
import sys
import importlib

from mcpainmkv.info import Info, SubtitleTrackInfo, AudioTrackInfo, VideoTrackInfo
from mcpainmkv.convert import convertMKV
from mcpainmkv.extract_bluray import extract_bluray

# BDSup2Sub Settings #
# Use java version
# BDSUP2SUB = ['/usr/bin/java', '-jar',
#              '~/.local/share/bdsup2sub/BDSup2Sub.jar']
# Use C++ version
BDSUP2SUB = ["bdsup2sub++"]


def main():
    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description="Manipulates Bluray remuxes for use in media server.",
    )

    subparser = parser.add_subparsers(title="Commands", dest="command", required=True)
    parser_convert = subparser.add_parser("convert", help="Start converting.")
    parser_convert.add_argument(
        "--config-name",
        dest="configName",
        help="Change the name of the config files.",
        type=str,
        default="info.json",
    )
    parser_convert.add_argument(
        "--clean",
        dest="clean",
        default=False,
        action=argparse.BooleanOptionalAction,
        help="Delete generated files.",
    )
    parser_convert.add_argument(
        "--clean-sources",
        dest="cleanSources",
        default=False,
        action=argparse.BooleanOptionalAction,
        help="Delete source files.",
    )

    parser_config = subparser.add_parser(
        "config", help="Generate 'info.json' configuration."
    )
    parser_config.add_argument(
        "--input",
        "-i",
        dest="sourceFile",
        type=str,
        help="Input '.mkv' file",
    )
    parser_config.add_argument(
        "--title",
        "-t",
        dest="configTitle",
        type=str,
        help="Title of output file.",
        default="Insert Title Here",
    )
    parser_config.add_argument(
        "--output",
        "-o",
        dest="configOutputFile",
        help="File name of output.",
        default="Insert Title Here.mkv",
    )
    parser_config.add_argument(
        "--nightmode",
        "-n",
        dest="configNightMode",
        help="Add 'nightmode' tracks based on track index.",
        nargs="+",
        type=int,
        default=[],
    )
    parser_config.add_argument(
        "--sup2srt",
        "-st",
        dest="configSup2Srt",
        help="Add text based subtitle tracks generated via 'sup2srt'.",
        nargs="+",
        type=int,
        default=[],
    )
    parser_config.add_argument(
        "--srt-filter",
        "-sf",
        dest="configSrtFilter",
        help="Enable subtitle filter for text based subtitles.",
        nargs="+",
        type=int,
        default=[],
    )
    parser_config.add_argument(
        "--languages",
        "-l",
        dest="configLangs",
        action="extend",
        nargs="+",
        type=str,
        help="List of audio/subtitle languages to keep.",
        default=[],
    )
    parser_config.add_argument(
        "--audio-languages",
        "-al",
        dest="configAudLangs",
        action="extend",
        nargs="+",
        type=str,
        help="List of audio languages to keep. (Overrides '--languages')",
        default=[],
    )
    parser_config.add_argument(
        "--sub-languages",
        "-sl",
        action="extend",
        dest="configSubLangs",
        nargs="+",
        type=str,
        help="List of subtitle languages to keep. (Overrides '--languages')",
        default=[],
    )
    parser_config.add_argument(
        "--vapoursynth",
        "-vs",
        dest="vapoursynth",
        help="Use external vapoursynth script for video processing.",
        type=str,
        default="",
    )
    parser_config.add_argument(
        "--config",
        "-c",
        dest="configFile",
        type=str,
        help="Config file output path.",
        default="info.json",
    )

    parser_sync_config = subparser.add_parser(
        "syncconfigs", help="Copy parts of an 'info.json' to a bunch of configs."
    )
    parser_sync_config.add_argument(
        "--base", "-b", dest="syncBase", type=str, help="base config file"
    )
    parser_sync_config.add_argument(
        "--configs",
        dest="syncConfigs",
        action="extend",
        nargs="+",
        type=str,
        help="List of config files.",
    )
    parser_sync_config.add_argument(
        "--video",
        "-v",
        dest="syncVideo",
        action=argparse.BooleanOptionalAction,
        help='Sync a property from config\'s "video" section.',
    )
    parser_sync_config.add_argument(
        "--audio",
        "-a",
        dest="syncAudio",
        action=argparse.BooleanOptionalAction,
        help="Sync a property from config's 'audio' section.",
    )
    parser_sync_config.add_argument(
        "--subtitles",
        "-s",
        dest="syncSubtitles",
        action=argparse.BooleanOptionalAction,
        help="Sync a property from config's 'subtitle' section.",
    )
    parser_extract_bluray = subparser.add_parser(
        "extract_bluray", help="Extracts Bluray into mkv files using 'mkvmerge'."
    )
    parser_extract_bluray.add_argument(
        "--bluray-directory",
        "-d",
        dest="blurayDirs",
        action="extend",
        nargs="+",
        help="Path to Bluray file structure.",
        type=str,
        default=[],
    )
    parser_extract_bluray.add_argument(
        "--config-file",
        "-c",
        dest="blurayJson",
        help="Path to '.json' config file.",
        type=str,
        default="extract_bluray.json",
    )
    parser_extract_bluray.add_argument(
        "--output-filename",
        "-o",
        dest="outFile",
        help="Name of '.mkv' files",
        type=str,
        default="source.mkv",
    )
    args = parser.parse_args()

    if "convert" in args.command:
        folders = []
        infoFile = args.configName
        if Path(infoFile).exists():
            folders.append(Path.cwd())
        else:
            for x in Path().cwd().iterdir():
                if x.is_dir():
                    if x.joinpath(infoFile).exists():
                        folders.append(x)

        cleaned = False
        if args.clean:
            cleanFiles(folders, infoFile)
            cleaned = True
        if args.cleanSources:
            cleanSourceFiles(folders, infoFile)
            cleaned = True
        if cleaned:
            return

        if not folders:
            print("No jobs found. Exiting...")
            return

        beGentlePlz()

        currentDir = Path.cwd()
        for folder in folders:
            print("Entering directory:", folder)
            os.chdir(folder)
            print(folders.index(folder), "out of", len(folders), "done.\n")
            convertMKV(infoFile)
            os.chdir(currentDir)
        return

    if "syncconfigs" in args.command:
        syncConfigs(
            args.syncBase,
            args.syncConfigs,
            args.syncVideo,
            args.syncAudio,
            args.syncSubtitles,
        )
        return

    if "config" in args.command:
        audLangs = args.configLangs
        subLangs = args.configLangs
        if args.configAudLangs:
            audLangs = args.configAudLangs
        if args.configSubLangs:
            subLangs = args.configSubLangs

        outConfig = Info(
            sourceMKV=args.sourceFile,
            title=args.configTitle,
            outputFile=args.configOutputFile,
            nightmode=args.configNightMode,
            sup2srt=args.configSup2Srt,
            srtFilter=args.configSrtFilter,
        )
        outConfig.filterLanguages(audLangs=audLangs, subLangs=subLangs)

        outConfig.videoInfo.vapoursynthScript = args.vapoursynth

        if args.configFile:
            print("Writting to '{}'".format(args.configFile))
            configPath = Path(args.configFile)
            configPath.write_text(str(outConfig))

        print(outConfig)
        return

    if "extract_bluray" in args.command:
        extract_bluray(args.blurayJson, args.blurayDirs, args.outFile)


def beGentlePlz():
    if importlib.util.find_spec("psutil"):
        import psutil

        psutil_process = psutil.Process()
        print("Setting process niceness to 15.")
        psutil_process.nice(15)
        print("Setting process ioniceness to idle.")
        if hasattr(psutil_process, "ionice"):
            psutil_process.ionice(psutil.IOPRIO_CLASS_IDLE)


def cleanSourceFiles(folders: list, infoFile: str):
    print("\nCleaning source video files")
    for folder in folders:
        info = Info(str(folder.joinpath(infoFile)))
        path = folder.joinpath(info.sourceMKV)
        if path.exists():
            print("Deleting:", path)
            path.unlink()


def cleanFiles(folders: list, infoFile: str):
    exclude = [Path(__file__).name, infoFile]
    for folder in folders:
        info = Info(str(folder.joinpath(infoFile)))
        exclude.append(info.sourceMKV)
        if info.videoInfo.vapoursynthScript != "":
            exclude.append(info.videoInfo.vapoursynthScript)

        for track in info.subInfo:
            if track.external:
                exclude.append(track.external)

        for file in folder.iterdir():
            if file.is_dir():
                continue
            if file.name not in exclude:
                print("Deleting", file)
                file.unlink()

        exclude.remove(info.sourceMKV)


def selectKeyFromDict(d: dict):
    keys = list(d.keys())
    print("-----------------------------------")
    for i in range(0, len(keys)):
        print("  {}: {}".format(i, keys[i]))

    selection = int(input("Which property? (between 0 and {}):".format(len(keys) - 1)))
    result = None
    while True:
        if selection >= 0 and selection < len(keys):
            result = keys[selection]
            break
        else:
            selection = int(
                input("Invalid input! (between 0 and {}):".format(len(keys) - 1))
            )

    return result


def syncConfigs(
    base: Path,
    configs: list[Path],
    videoInfo: bool = False,
    audioInfo: bool = False,
    subInfo: bool = False,
):
    base = Path(base)
    configs = [Path(x) for x in configs]

    baseInfo: Info = Info(jsonFile=base)

    if videoInfo:
        print("Syncing VideoInfo")
        baseVideo: VideoTrackInfo = baseInfo.videoInfo
        propToCopy = selectKeyFromDict(dict(baseVideo))

        for config in configs:
            configInfo = Info(jsonFile=config)
            videoDict = dict(configInfo.videoInfo)
            baseProp = dict(baseVideo)[propToCopy]
            videoDict[propToCopy] = baseProp
            configInfo.videoInfo = VideoTrackInfo(jsonData=videoDict)

            print("Updating:", config)
            config.write_text(str(configInfo))
    if audioInfo:
        print("Syncing Audio Info")
        baseAudInfo: list[AudioTrackInfo] = baseInfo.audioInfo

        for config in configs:
            configInfo = Info(jsonFile=config)
            configInfo.audioInfo = baseAudInfo

            print("Updating:", config)
            config.write_text(str(configInfo))
    if subInfo:
        print("Syncing Subtitle Info")
        baseSubInfo: list[SubtitleTrackInfo] = baseInfo.subInfo

        for config in configs:
            configInfo = Info(jsonFile=config)
            configInfo.subInfo = baseSubInfo

            print("Updating:", config)
            config.write_text(str(configInfo))

    return


if __name__ == "__main__":
    main()
