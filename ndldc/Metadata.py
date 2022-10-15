import requests
import lxml.html


class Metadata:
    def __init__(self, dictionary):
        self.dictionary = dictionary

    def __getitem__(self, arg):
        key = f"({arg})"
        for k, v in self.dictionary.items():
            if key in k:
                return v

    @staticmethod
    def from_tree(tree):
        dts = tree.xpath('//dl[@class="detail-metadata-list"]/dt')
        dds = tree.xpath('//dl[@class="detail-metadata-list"]/dd')
        metadata = {}
        for dt, dd in zip(dts, dds):
            key = dt.text_content().strip()
            value = dd.text_content().strip()
            metadata[key] = value
        return Metadata(metadata)
