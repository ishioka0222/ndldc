import ast
import lxml.html
import re

from .Metadata import Metadata


class Frame:
    def __init__(self, tree):
        self.tree = tree
        self.metadata = Metadata.from_tree(tree)

    def get_hidden_input_value(self, key):
        input = self.tree.xpath(f'//input[@id="{key}"]')[0]
        value = input.attrib["value"]
        return value

    def get_content_image_root_path(self):
        value = self.get_hidden_input_value("viewer-content-image-root-path")
        return value

    def get_content_id(self):
        value = self.get_hidden_input_value("viewer-content-id")
        return value

    def get_content_custom_param(self):
        value = self.get_hidden_input_value("viewer-content-custom-param")
        data = ast.literal_eval(value)
        return data

    def get_frame_count(self):
        a = self.tree.xpath('//a[@class="ndltree-item ndltree-label"]')[0]
        text = a.text_content()
        match = re.match(r"(.+) \[(?P<frame_count>\d+)\]", text)
        frame_count = int(match.group("frame_count"))
        return frame_count

    @staticmethod
    def from_html(html):
        tree = lxml.html.fromstring(html)
        return Frame(tree)
