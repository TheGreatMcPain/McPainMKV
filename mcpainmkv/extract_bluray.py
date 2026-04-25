from pathlib import Path
import makemkv
from iso639 import is_language
from mcpainmkv.info import Info


class extractBluray:
    def __init__(self, blurayPath: str):
        self.blurayPath = blurayPath
        self.discInfo = makemkv.MakeMKV(self.blurayPath).info()

    def createMKV(self, blurayFile, outFile):
        if Path(outFile).exists():
            return

        outDir = Path(outFile).absolute().parent
        if not Path(outDir).exists():
            outDir.mkdir()

        if outDir.glob("*.mkv"):
            for x in outDir.glob("*.mkv"):
                x.unlink()

        with makemkv.ProgressParser() as progress:
            mkvmaker = makemkv.MakeMKV(self.blurayPath, progress_handler=progress.parse_progress)
            blurayTitle = self.selectTitle(blurayFile)
            if not blurayTitle:
                print("Bluray title, or file doesn't exist!:", blurayFile)
                return

            index = self.discInfo["titles"].index(blurayTitle)
            mkvmaker.mkv(index, outDir)

        for x in outDir.glob("*.mkv"):
            x.rename(outDir.joinpath(outFile))

    def getBlurayInfo(self, infoFileName: str):
        """
        Asks that user for information on a BluRay directory,
        and will export create a json file with the infomation.
        """

        print("BluRay Root:", self.blurayPath)
        while True:
            print()
            print(
                "Type filename or title number (Ex: 00800.mpls or 00510.m2ts or 1) ",
                end="",
            )
            fileName = input("(Type 'done' if finished): ")
            if "done" in fileName:
                break

            blurayTitle = self.selectTitle(fileName)
            if not blurayTitle:
                print(blurayTitle, "does not exist.")
                continue

            self.printTitleInfo(blurayTitle)

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

            nightmode = input("List audio track numbers to apply nightmodes to. (ex: 1,2): ").split(
                ","
            )
            sup2srt = input("List subtitle numbers to apply sup2srt to. (ex: 1,2): ").split(",")
            srtFilter = input("List subtitle numbers to apply srt-filter to. (ex: 1,2): ").split(
                ","
            )

            title = input("What's the title of this file?: ")
            info = Info(
                nightmode=[int(x) for x in nightmode if x.isdigit()],
                sup2srt=[int(x) for x in sup2srt if x.isdigit()],
                srtFilter=[int(x) for x in srtFilter if x.isdigit()],
                audLangs=audioLangs,
                subLangs=subtitleLangs,
            )
            info.blurayFile = fileName
            info.blurayPath = self.blurayPath
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
                    Path("extras", folder).mkdir(parents=True)
            else:
                folder = input("Type the folder name for this title: ")
                outputInfo = Path(folder).joinpath(outputInfo)
                if not Path(folder).exists():
                    Path(folder).mkdir()
            outputInfo.write_text(str(info))

    # input can be a filename ".m2ts, .mpls" or a title number based on MakeMKV's output.
    def selectTitle(self, input: str):
        if ".mpls" in input or ".m2ts" in input:
            return next(x for x in self.discInfo["titles"] if input == x["source_filename"])

        if input.isdigit() and int(input) in range(len(self.discInfo["titles"])):
            return self.discInfo["titles"][int(input)]

        return None

    def printTitleInfo(self, title):
        print("File:", title["source_filename"])
        print("Length:", title["length"])
        counter = 0
        for stream in title["streams"]:
            print("", counter, end=" ")
            if stream["type"] == "subtitles":
                counter -= 1
            for key in stream.keys():
                print(stream[key], end=" ")
            print()

            counter += 1
