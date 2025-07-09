import re
from lxml.html import fromstring, tostring


class HtmlParser():
    
    def __init__(self):
        pass


    def only_skeleton(self, html):
        try:
            tree = fromstring(html)
            # 移除所有注释
            for comment in tree.xpath('//comment()'):
                parent = comment.getparent()
                if parent is not None:
                    parent.remove(comment)

            # 移除所有 script 标签及其内容
            for script in tree.xpath('//script'):
                parent = script.getparent()
                if parent is not None:
                    parent.remove(script)

            # 移除所有 style 标签及其内容
            for style in tree.xpath('//style'):
                parent = style.getparent()
                if parent is not None:
                    parent.remove(style)

            # 移除所有标签的属性
            for element in tree.iter():
                element.attrib.clear()

            # 从根节点开始移除没有文本的元素
            self.prune_empty_elements(tree)

            # 将处理后的树转换为字符串
            clean_html_plus = tostring(tree, encoding='unicode')
            clean_html_plus = re.sub(r'>\s+<', '><', clean_html_plus)
            return clean_html_plus.encode("utf-8").decode("utf-8")
        except Exception as e:
            return ""


    def only_skeleton2(self, html):
        try:
            tree = fromstring(html)
            # 移除所有注释
            for comment in tree.xpath('//comment()'):
                parent = comment.getparent()
                if parent is not None:
                    parent.remove(comment)

            # 移除所有 script 标签及其内容
            for script in tree.xpath('//script'):
                parent = script.getparent()
                if parent is not None:
                    parent.remove(script)

            # 移除所有 style 标签及其内容
            for style in tree.xpath('//style'):
                parent = style.getparent()
                if parent is not None:
                    parent.remove(style)

            # 移除所有标签的属性
            for element in tree.iter():
                element.attrib.clear()

            # 从根节点开始移除没有文本的元素
            # self.prune_empty_elements(tree)

            # 将处理后的树转换为字符串
            clean_html_plus = tostring(tree, encoding='unicode')
            clean_html_plus = re.sub(r'>\s+<', '><', clean_html_plus)
            return clean_html_plus.encode("utf-8").decode("utf-8")
        except Exception as e:
            return ""


    # def has_text(self, element):
    #     """
    #     判断元素是否包含文本
    #     """
    #     if element.text and element.text.strip():
    #         return True
    #     for child in element:
    #         if self.has_text(child):
    #             return True
    #     return False
    def has_text(self, element):
        """
        判断元素是否包含文本
        """
        if element.text and element.text.strip():
            return True
        if element.tail and element.tail.strip():
            return True
        for child in element:
            if self.has_text(child):
                return True
        return False


    # def prune_empty_elements(self, parent):
    #     """
    #     递归移除没有文本的子元素
    #     """
    #     children_to_remove = []
    #     for child in parent:
    #         if not self.has_text(child):
    #             children_to_remove.append(child)
    #         else:
    #             self.prune_empty_elements(child)
    #     for child in children_to_remove:
    #         parent.remove(child)
    def prune_empty_elements(self, parent):
        """
        递归移除没有文本的子元素
        """
        children_to_remove = []
        for child in parent:
            if child.tag == 'br':
                continue  # 跳过 <br> 标签
            if not self.has_text(child):
                children_to_remove.append(child)
            else:
                self.prune_empty_elements(child)
        for child in children_to_remove:
            parent.remove(child)


if __name__ == "__main__":
    import requests
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0"}
    response = requests.get("https://www.research.ed.ac.uk/en/persons/ian-deary-2", timeout=2, headers=headers)
    clean_html = HtmlParser().only_skeleton(response.text)
    with open("cleaned.html", "w", encoding="utf-8") as f:
        f.write(clean_html)