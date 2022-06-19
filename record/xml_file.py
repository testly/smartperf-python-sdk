import xml.etree.ElementTree as ET


class GetPosition:
    # 定义并初始化的元素的边界值
    bounds = [0, 0, 0, 0]
    # 定义并初始化的元素的深度
    level = 0
    # 定义并初始化该元素的所有信息
    xmlLine = []
    # 定义并初始化该元素的id信息
    resource_id = ""

    def __init__(self, data, dot):
        # 经处理后的屏幕信息，类型：list
        self.data = data
        # 点击位置的坐标
        self.dot = dot
        self.get_xml_xpath()

    def get_xml_xpath(self):
        """
        获取资源resource-id
        :return:
        """
        # 遍历每行的信息
        for line in self.data:
            # 判断line[-1]是否为字典类型
            if isinstance(line[-1], dict):
                # 获取元素的边界值信息，并且将str格式化：[0,1080][0,1920]->['0','1080','0','1920']
                bounds = str(line[-1].get("bounds")).replace("][", ',').replace("[", "").replace("]", "").split(",")
                # 判断元素是否正常
                if len(bounds) == 4:
                    x1, y1, x2, y2 = int(bounds[0]), int(bounds[1]), int(bounds[2]), int(bounds[3])
                    # 判断该点的位置，是否处于该元素边界内
                    if x1 <= self.dot[0] <= x2 and y1 <= self.dot[1] <= y2:
                        # 找出满足条件中深度最大的元素
                        if int(line[1]) > self.level:
                            self.level = int(line[1])
                            self.bounds = [x1, y1, x2, y2]
                            self.xmlLine = line
                            self.resource_id = line[-1].get("resource-id")


class XmlFile:
    unique_id = 1

    def walk_xml(self, root_node, level, result_list):
        """
        遍历所有的节点
        :param root_node:
        :param level:
        :param result_list:
        :return:
        """
        temp_list = [self.unique_id, level, root_node.tag, root_node.attrib]
        result_list.append(temp_list)
        self.unique_id += 1

        # 遍历每个子节点
        children_node = root_node.getchildren()
        if len(children_node) == 0:
            return
        for child in children_node:
            self.walk_xml(child, level + 1, result_list)
        return

    def parse_xml_data(self, file_name=None, xpath=None):
        """
        通过文件名解析xml文件
        :param file_name:
        :param xpath:xml的字符串
        :return:
        """
        if not file_name and not xpath:
            file = open(file_name, "w", encoding='utf-8-sig')
            file.write(xpath)
            file.close()
        level = 1  # 节点的深度从1开始
        result_list = []
        root = ET.parse(file_name).getroot()
        self.walk_xml(root, level, result_list)
        return result_list
