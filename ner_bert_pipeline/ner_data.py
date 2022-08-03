import datasets
import logging
import os


_TRAINING_FILE = "proj.txt"
_DEV_FILE = "proj.txt"
_TEST_FILE = "proj.txt"


class ProjectConfig(datasets.BuilderConfig):

    def __init__(self, **kwargs):
        super(ProjectConfig, self).__init__(**kwargs)


class ProjectData(datasets.GeneratorBasedBuilder):

    BUILDER_CONFIGS = [
        ProjectConfig(name="project", version=datasets.Version(
            "1.0.0"), description="project dataset"),
    ]

    def _info(self):
        return datasets.DatasetInfo(
            description="project data",
            features=datasets.Features(
                {
                    "id": datasets.Value("string"),
                    "tokens": datasets.Sequence(datasets.Value("string")),
                    "ner_tags": datasets.Sequence(
                        datasets.features.ClassLabel(
                            names=[
                                "O",
                                "B-projectName",
                                "I-projectName",
                                "B-timeRange",
                                "I-timeRange",
                                "B-title",
                                "I-title",
                                "B-company",
                                "I-company"
                            ]
                        )
                    ),
                }
            ),
            supervised_keys=None,
            homepage="",
            citation="",
        )

    def _split_generators(self, dl_manager):
        return [
            datasets.SplitGenerator(name=datasets.Split.TRAIN, gen_kwargs={
                                    "filepath": os.path.join(self.config.data_dir, _TRAINING_FILE)}),
            datasets.SplitGenerator(name=datasets.Split.VALIDATION, gen_kwargs={
                                    "filepath": os.path.join(self.config.data_dir, _DEV_FILE)}),
            datasets.SplitGenerator(name=datasets.Split.TEST, gen_kwargs={
                                    "filepath": os.path.join(self.config.data_dir, _TEST_FILE)}),
        ]

    def _generate_examples(self, filepath):
        '''读取的文件的每行格式：token tag\n'''
        logging.info("⏳ Generating examples from = %s", filepath)
        with open(filepath, encoding="utf-8") as f:
            guid = 0  # 每条数据的id
            tokens = []  # 每条数据的token
            ner_tags = []  # 每条数据的tag
            for line in f:
                # 如果遇到文件开头，每条数据分界，文件结尾，就生成一条数据
                if line == "" or line == "\n":
                    if tokens:
                        yield guid, {
                            "id": str(guid),
                            "tokens": tokens,
                            "ner_tags": ner_tags,
                        }
                        guid += 1
                        tokens = []
                        ner_tags = []
                else:
                    splits = line.split(" ")
                    tokens.append(splits[0])
                    ner_tags.append(splits[-1].rstrip())
