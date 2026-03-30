from pathlib import Path
import makemkv
from iso639 import is_language
from mcpainmkv.info import Info, InfoGenerateOptions


def printTitleInfo(title):
    print("File:", title["source_filename"])
    print("Length:", title["length"])
    counter = 0
    for stream in title["streams"]:
        if stream["type"] == "audio":
            print(
                "",
                counter,
                stream["type"],
                stream["metadata_langcode"],
                stream["codec_id"],
                stream["downmix"],
                stream["samplerate"],
                stream["bitrate"],
            )
        elif stream["type"] == "subtitles":
            if "(forced only)" in stream["information"]:
                counter -= 1
            print(
                "",
                counter,
                stream["type"],
                stream["metadata_langcode"],
                stream["codec_id"],
                stream["information"],
            )
        else:
            print(
                "",
                counter,
                stream["type"],
                stream["metadata_langcode"],
                stream["codec_id"],
                stream["dimensions"],
                stream["aspect_ratio"],
                stream["framerate"],
                stream["information"],
            )
        counter += 1


def config_bluray(blurayDir: str, jsonFileName: str):
    getBlurayInfo(blurayDir, jsonFileName)


def extract_bluray(jsonFiles: list[str], outFile: str):
    for jsonFile in jsonFiles:
        jsonPath = Path(jsonFile).resolve()
        info = Info(jsonPath)
        disc = makemkv.MakeMKV(info.blurayPath)
        discInfo = disc.info()

        createMKV(
            discInfo,
            info.blurayPath,
            info.blurayFile,
            Path(jsonPath.parent, outFile),
        )

        jsonPath.write_text(
            str(Info(jsonFile=jsonPath, sourceMKV=str(Path(jsonPath.parent, outFile))))
        )


def createMKV(discInfo, blurayDir, blurayFile, outFile):
    if Path(outFile).exists():
        return

    outDir = Path(outFile).absolute().parent
    if not Path(outDir).exists():
        outDir.mkdir()

    if outDir.glob("*.mkv"):
        for x in outDir.glob("*.mkv"):
            x.unlink()

    with makemkv.ProgressParser() as progress:
        mkvmaker = makemkv.MakeMKV(blurayDir, progress_handler=progress.parse_progress)
        for title in discInfo["titles"]:
            if blurayFile in title["source_filename"]:
                index = discInfo["titles"].index(title)
                mkvmaker.mkv(index, outDir)

    for x in outDir.glob("*.mkv"):
        x.rename(outDir.joinpath(outFile))


def titleExists(discInfo, blurayFile: str):
    for title in discInfo["titles"]:
        if blurayFile == title["source_filename"]:
            return True
    return False


def getTitleFromFile(discInfo, blurayFile):
    for title in discInfo["titles"]:
        if blurayFile == title["source_filename"]:
            return title


def getBlurayInfo(BluRayPath: Path, infoFileName: str):
    """
    Asks that user for information on a BluRay directory,
    and will export create a json file with the infomation.
    """
    blurayInfo = {}
    blurayInfo["blurayDir"] = str(BluRayPath)

    disc = makemkv.MakeMKV(BluRayPath)
    discInfo = disc.info()

    print("BluRay Root:", BluRayPath)
    while True:
        print()
        print("Type filename (Ex: 00800.mpls or 00510.m2ts) ", end="")
        fileName = input("(Type 'done' if finished): ")
        if "done" in fileName:
            break
        if not titleExists(discInfo, fileName):
            print(fileName, "does not exist.")
            continue

        printTitleInfo(getTitleFromFile(discInfo, fileName))
        audioLangs = []
        while not audioLangs:
            audioLangs = input(
                "Please list what audio languages to keep (ex: eng,jpn): "
            ).split(",")
            for lang in audioLangs:
                if not is_language(lang):
                    print("Error", lang, "is not a language.")
                    audioLangs = []
                    break
        subtitleLangs = []
        while not subtitleLangs:
            subtitleLangs = input(
                "Please list what subtitle languages to keep (ex: eng,jpn): "
            ).split(",")
            for lang in subtitleLangs:
                if not is_language(lang):
                    print("Error", lang, "is not a language.")
                    subtitleLangs = []
                    break

        nightmode = input(
            "List audio track numbers to apply nightmodes to. (ex: 1,2): "
        ).split(",")
        sup2srt = input("List subtitle numbers to apply sup2srt to. (ex: 1,2): ").split(
            ","
        )
        srtFilter = input(
            "List subtitle numbers to apply srt-filter to. (ex: 1,2): "
        ).split(",")

        title = input("What's the title if this file?: ")
        info = Info(
            nightmode=[int(x) for x in nightmode],
            sup2srt=[int(x) for x in sup2srt],
            srtFilter=[int(x) for x in srtFilter],
            audLangs=audioLangs,
            subLangs=subtitleLangs,
        )
        info.blurayFile = fileName
        info.blurayPath = BluRayPath
        info.title = title
        info.outputFile = title + ".mkv"

        extra = input("Is this an extra feature (y or n): ")
        while extra.lower() not in ["y", "n"]:
            print("Invalid input: must be 'y' or 'n'")
            extra = input("Is this an extra feature (y or n): ")

        outputInfo = Path(infoFileName)
        if "y" in extra.lower():
            folder = input("Type the folder name for this title: ")
            outputInfo = Path("extras", folder).joinpath(outputInfo)
            if not Path("extras", folder).exists():
                Path("extras", folder).mkdir()
        else:
            folder = input("Type the folder name for this title: ")
            outputInfo = Path(folder).joinpath(outputInfo)
            if not Path(folder).exists():
                Path(folder).mkdir()
        outputInfo.write_text(str(info))
