import os
import jieba
import re
import json
from typing import List, Dict, Optional

class DocumentProcessor:
    """文档处理类"""
  
    def tokenize_layer(self, layer: str) -> List[str]:
        """
        Tokenize层级
        """
        
        if "conversation" in layer:
            return ["conversation"]
        elif "objective" in layer:
            return ["objective"]
        elif "init" in layer:
            return ["init"]
        elif "profile" in layer:
            return ["profile"]
        else:
            return []
    
    def tokenize_text(self, text: str) -> List[str]:
        """
        Tokenize文本
        
        Args:
            text: 输入文本
            
        Returns:
            Tokenized文本列表
        """
        # 对中文文本使用jieba分词
        if any('\u4e00' <= char <= '\u9fff' for char in text):  # 检测是否包含中文字符
            words = list(jieba.cut(text))
        else:
            # 对英文文本使用正则表达式
            words = re.findall(r'\b\w+\b', text)
        
        # 过滤停用词和短词
        stopwords = {"的", "了", "和", "是", "在", "有", "与", "为", "以", "及", "对", "上", "中", "下", 
                    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", 
                    "be", "been", "being", "in", "on", "at", "to", "for", "with", "by",
                    "about", "against", "between", "into", "through", "during", "before",
                    "after", "above", "below", "from", "up", "down", "of", "off", "over",
                    "under", "again", "further", "then", "once", "here", "there", "when",
                    "where", "why", "how", "all", "any", "both", "each", "few", "more",
                    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
                    "same", "so", "than", "too", "very", "can", "will", "just", "should",
                    "now", "d", "ll", "m", "o", "re", "s", "t", "ve", "y", "ain", "aren",
                    "couldn", "didn", "doesn", "hadn", "hasn", "haven", "isn", "ma",
                    "mightn", "mustn", "needn", "shan", "shouldn", "wasn", "weren", "won"}
        
        words = [word for word in words if len(word) >= 2 and word.lower() not in stopwords]
        
        return words