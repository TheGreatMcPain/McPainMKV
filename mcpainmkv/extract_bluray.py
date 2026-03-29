from pathlib import Path
import makemkv
import json


def extract_bluray(jsonFile: str, blurayDirs: list[str], outFile: str):
    jsonFile = Path(jsonFile)
    blurayInfoList = []

    selection = "n"
    if jsonFile.exists():
        print(jsonFile, "found.")
        selection = input("Resume with it? (y or n): ")

    if selection == "y":
        blurayInfoList = json.loads(jsonFile.read_text())
        if type(blurayInfoList) is dict:
            blurayInfoList = [blurayInfoList]

        for blurayRoot in blurayDirs:
            blurayPath = Path(blurayRoot)

            if not isBluray(blurayPath):
                print(blurayPath, "is not a BluRay Directory.")
                return

            if str(blurayPath) not in [x["blurayDir"] for x in blurayInfoList]:
                selection = input(
                    "Add {} to {}. (y or n): ".format(blurayPath, jsonFile)
                )
            if selection == "y":
                blurayInfo = getBlurayInfo(blurayPath)
                blurayInfoList.append(blurayInfo)
                jsonFile.write_text(json.dumps(blurayInfoList))
    else:
        if len(blurayDirs) == 0:
            print(
                jsonFile.relative_to(Path.cwd()),
                "not found!",
                "Bluray directory required.",
            )
            return

        for blurayRoot in blurayDirs:
            blurayPath = Path(blurayRoot)

            if not isBluray(blurayPath):
                print(blurayPath, "is not a BluRay Directory.")
                return

            blurayInfo = getBlurayInfo(blurayPath)
            blurayInfoList.append(blurayInfo)
            jsonFile.write_text(json.dumps(blurayInfoList))

    blurayInfoList = filterBlurayInfo(blurayInfoList)
    for blurayInfo in blurayInfoList:
        batchCreateMKVs(blurayInfo["blurayDir"], blurayInfo["titles"], outFile)


def isBluray(blurayPath: Path) -> bool:
    return blurayPath.joinpath("BDMV", "index.bdmv").exists()


def filterBlurayInfo(blurayInfo: list) -> list[dict]:
    newInfo = []
    for root in blurayInfo:
        blurayDir = Path(root["blurayDir"])
        if not blurayDir.exists():
            print(blurayDir, "doesn't exist! skipping...")
            continue
        if not isBluray(blurayDir):
            print(blurayDir, "isn't a Bluray. skipping...")
            continue

        titles = []
        for title in root["titles"]:
            blurayFile = getBluRayFilePath(root["blurayDir"], title["filename"])
            if not blurayFile.exists():
                print(
                    blurayFile,
                    "doesn't exist! Bluray. skipping bluray...",
                )
                print("Bluray folder is either incomplete or incorrect.\n")
                titles = []
                break
            titles.append(title)

        if len(titles) > 0:
            newInfo.append(root)

    return newInfo


def batchCreateMKVs(BluRayDir, titles, outFile):
    counter = 0
    with makemkv.ProgressParser() as progress:
        disc = makemkv.MakeMKV(BluRayDir, progress_handler=progress.parse_progress)
    for title in titles:
        print()
        print(counter, "out of", len(titles), "done")
        output = ""
        fileName = title["filename"]
        inFile: Path = getBluRayFilePath(BluRayDir, fileName)
        if not inFile.exists():
            print("Oof!! Something must of broke!")
            exit(1)
        if "n" in title["main"]:
            extrasPath = Path("extras")
            if not extrasPath.is_dir():
                extrasPath.mkdir()
            output = extrasPath.joinpath(title["folder"])
        else:
            output = Path(title["folder"])
        if not output.is_dir():
            output.mkdir()

        # if output.:
        #    print(output, "exists!! skipping...")
        #    continue

        discInfo = disc.info()
        for title in discInfo["titles"]:
            if fileName in title["source_filename"]:
                index = discInfo["titles"].index(title)
                disc.mkv(index, output)

        counter += 1


def getBluRayFilePath(BluRayPath: Path, fileName: Path) -> Path:
    BluRayPath = Path(BluRayPath)
    fileName = Path(fileName)
    """
    Returns that full path of a m2ts/mpls file.
    """
    ext = fileName.suffix

    filePath = BluRayPath.joinpath("BDMV")
    if ".m2ts" in ext:
        filePath = filePath.joinpath(filePath, Path("STREAM"), fileName)
    if ".mpls" in ext:
        filePath = filePath.joinpath(filePath, Path("PLAYLIST"), fileName)

    return filePath


def titleExists(BluRayPath: Path, fileName: Path):
    BluRayPath = Path(BluRayPath)
    fileName = Path(fileName)
    """
    Checks if a file exists in the BluRay.
    """
    ext = fileName.suffix
    if ext not in [".m2ts", ".mpls"]:
        print(ext, "Is not a BluRay file extention.")
        return False

    return getBluRayFilePath(BluRayPath, fileName).exists()


def getBlurayInfo(BluRayPath: Path):
    """
    Asks that user for information on a BluRay directory,
    and will export create a json file with the infomation.
    """
    blurayInfo = {}
    blurayInfo["blurayDir"] = str(BluRayPath)
    titles = []

    print("BluRay Root:", BluRayPath)
    while True:
        print()
        title = {}
        print("Type filename (Ex: 00800.mpls or 00510.m2ts) ", end="")
        fileName = input("(Type 'done' if finished): ")
        if "done" in fileName:
            break
        if not titleExists(BluRayPath, Path(fileName)):
            print(fileName, "does not exist.")
            continue
        extra = input("Is this an extra feature (y or n): ")
        while extra.lower() not in ["y", "n"]:
            print("Invalid input: must be 'y' or 'n'")
            extra = input("Is this an extra feature (y or n): ")
        if "y" in extra.lower():
            title["main"] = "no"
            folder = input("Type the folder name for this title: ")
            title["folder"] = folder
        else:
            title["main"] = "yes"
            folder = input("Type the folder name for this title: ")
            title["folder"] = folder
        title["filename"] = str(fileName)
        titles.append(title)
    blurayInfo["titles"] = titles
    return blurayInfo
