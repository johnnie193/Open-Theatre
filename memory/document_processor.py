import os
import jieba
import re
import json
from typing import List, Dict, Optional
from utils import logger

class DocumentProcessor:
    """文档处理类"""
    
#     def __init__(self):

#         # BM25检索相关
#         self.bm25_index = None
#         self.bm25_corpus = None
#         self.bm25_chunk_mapping = []
        
#     async def process_document(self, force_reprocess: bool = False):
#         """
#         处理文档并存储向量嵌入
        
#         Args:
#             force_reprocess: 是否强制重新处理
#         """
#         # 检查是否需要处理
#         if self.processed_chunks is not None and not force_reprocess:
#             return
#         # 新增：如果向量数据库已存在且有数据，直接加载BM25索引
#         if self.vector_store.has_data() and not force_reprocess:
#             logging.info("检测到向量数据库已存在且有数据，跳过文档分割和嵌入。")
#             self.processed_chunks = self.vector_store.load_all_chunks()
#             self._create_bm25_index(self.processed_chunks)
#             logging.info("BM25索引创建完成")
#             return
#         logging.info(f"处理文档: {self.doc_path}")
        
#         # 处理Markdown文件
#         chunks = self.md_processor.process_markdown_file(self.doc_path)
#         logging.info(f"文档分割完成，共 {len(chunks)} 个块")
        
#         # 获取文本嵌入
#         texts = [chunk["content"] for chunk in chunks]
#         embeddings = self.embeddings.get_embeddings(texts)
#         logging.info("向量嵌入计算完成")
        
#         # 存储到向量数据库
#         self.vector_store.store_embeddings(chunks, embeddings)
#         logging.info("向量存储完成")
        
#         # 创建BM25索引
#         self._create_bm25_index(chunks)
#         logging.info("BM25索引创建完成")
        
#         # 保存处理后的文档块
#         self.processed_chunks = chunks
        
#     def _create_bm25_index(self, chunks: List[Dict]):
#         """
#         创建BM25索引
        
#         Args:
#             chunks: 文档块列表
#         """
#         # 获取文本内容列表
#         texts = [chunk["content"] for chunk in chunks]
#         # Tokenize文本
#         tokenized_corpus = [self._tokenize_text(text) for text in texts]
#         # 创建BM25索引
#         self.bm25_index = BM25Okapi(tokenized_corpus)
        
#         # 保存文本内容和块索引的映射
#         self.bm25_corpus = texts
#         self.bm25_chunk_mapping = list(range(len(chunks)))
        

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
    
        
#     async def _analyze_with_llm(self, user_input: str, retrieved_contents: List[str], prompt: str = "") -> List[dict]:
#         """
#         使用LLM批量分析用户输入与多个检索内容的相关性（异步版本）
        
#         Args:
#             user_input: 用户输入的内容
#             retrieved_contents: 检索到的内容列表
#             prompt: 自定义提示词
        
#         Returns:
#             LLM分析报告列表
#         """
#         logging.info(f"\n{'='*50}\n开始LLM分析\n{'='*50}")
#         logging.info(f"用户输入: {user_input}")
#         logging.info(f"检索内容数量: {len(retrieved_contents)}")
        
#         # 构建批量提示词
#         if not prompt:
#             prompt = """请分析以下用户输入与检索内容的相关性。请严格按照JSON格式返回分析结果。

# 用户输入: {user_input}

# 检索内容列表:
# {retrieved_contents}

# 请为每个检索内容生成一个JSON对象，包含以下字段：
# - judgment_result: 判断结果（完全一致/高度相关/部分相关/不相关）
# - explanation: 简要说明判断理由
# - relevance_score: 相关性评分（0-1）
# - content: 该检索内容的原文

# 重要说明：
# 1. 必须为每个检索内容生成一个分析结果，返回结果数量必须与检索内容数量相同
# 2. 请直接返回JSON数组，不要包含任何其他文字说明
# 3. 即使相关性较低，也要返回分析结果，将relevance_score设置为较低的值
# 4. 不要遗漏任何检索内容

# 示例格式：
# [
#     {{
#         "judgment_result": "完全一致",
#         "explanation": "检索内容与用户输入完全匹配",
#         "relevance_score": 1.0,
#         "content": "原文内容"
#     }}
# ]"""

#         # 构建检索内容字符串
#         content_str = "\n\n".join([f"[内容 {i+1}]\n{content}" for i, content in enumerate(retrieved_contents)])
        
#         # 替换占位符
#         final_prompt = prompt.format(
#             user_input=user_input,
#             retrieved_contents=content_str
#         )
        
#         logging.info(f"提示词长度: {len(final_prompt)}字符")
#         logging.info(f"提示词前100个字符: {final_prompt[:100]}...")
        
#         try:
#             # 调用LLM
#             logging.info("正在调用LLM...")
#             analysis = await async_chat([{"role": "user", "content": final_prompt}])
#             logging.info(f"LLM返回内容长度: {len(analysis)}字符")
#             logging.info(f"LLM返回内容前200个字符:\n{analysis[:200]}")
            
#             # 尝试解析JSON
#             try:
#                 # 清理可能的markdown代码块标记
#                 logging.info("清理markdown代码块标记...")
#                 analysis = analysis.replace("```json", "").replace("```", "").strip()
#                 logging.info(f"清理后的内容前200个字符:\n{analysis[:200]}")
                
#                 logging.info("尝试解析JSON...")
#                 result = json.loads(analysis)
#                 logging.info(f"JSON解析成功，结果类型: {type(result)}")
                
#                 # 验证结果格式
#                 if isinstance(result, list):
#                     logging.info(f"结果是列表，长度: {len(result)}")
                    
#                     # 如果结果数量不足，补充默认结果
#                     if len(result) < len(retrieved_contents):
#                         logging.warning(f"LLM返回结果数量({len(result)})少于检索内容数量({len(retrieved_contents)})，补充默认结果")
#                         for i in range(len(result), len(retrieved_contents)):
#                             result.append({
#                                 "judgment_result": "未分析",
#                                 "explanation": "LLM未返回此内容的分析结果",
#                                 "relevance_score": 0.0,
#                                 "content": retrieved_contents[i]
#                             })
                    
#                     # 确保每个项目都有必要的字段
#                     validated_results = []
#                     for i, item in enumerate(result):
#                         logging.info(f"验证第 {i+1} 个项目...")
#                         if isinstance(item, dict):
#                             missing_fields = [k for k in ["judgment_result", "explanation", "relevance_score"] if k not in item]
#                             if missing_fields:
#                                 logging.warning(f"项目 {i+1} 缺少必要字段: {missing_fields}")
#                                 # 补充缺失字段
#                                 for field in missing_fields:
#                                     if field == "judgment_result":
#                                         item[field] = "未分析"
#                                     elif field == "explanation":
#                                         item[field] = "缺少必要字段"
#                                     elif field == "relevance_score":
#                                         item[field] = 0.0
                        
#                             # 补充content字段
#                             if "content" not in item:
#                                 logging.info(f"项目 {i+1} 补充content字段")
#                                 item["content"] = retrieved_contents[i]
                            
#                             validated_results.append(item)
#                             logging.info(f"项目 {i+1} 验证通过")
#                         else:
#                             logging.warning(f"项目 {i+1} 不是字典类型，创建默认结果")
#                             validated_results.append({
#                                 "judgment_result": "格式错误",
#                                 "explanation": "LLM返回的结果格式不正确",
#                                 "relevance_score": 0.0,
#                                 "content": retrieved_contents[i]
#                             })
                    
#                     if validated_results:
#                         logging.info(f"验证通过的结果数量: {len(validated_results)}")
#                         return validated_results
#                     else:
#                         logging.warning("没有验证通过的结果")
                
#                 # 如果解析失败或格式不正确，返回默认结果
#                 logging.warning("返回默认结果")
#                 return [{
#                     "judgment_result": "解析失败",
#                     "explanation": "无法解析LLM返回的JSON格式",
#                     "relevance_score": 0.0,
#                     "content": content
#                 } for content in retrieved_contents]
                
#             except json.JSONDecodeError as e:
#                 logging.error(f"JSON解析失败: {str(e)}")
#                 logging.error(f"解析失败的内容:\n{analysis}")
#                 return [{
#                     "judgment_result": "解析失败",
#                     "explanation": "LLM返回内容不是有效的JSON格式",
#                     "relevance_score": 0.0,
#                     "content": content
#                 } for content in retrieved_contents]
                
#         except Exception as e:
#             logging.error(f"LLM分析失败: {str(e)}")
#             return [{
#                 "judgment_result": "分析失败",
#                 "explanation": f"LLM调用失败: {str(e)}",
#                 "relevance_score": 0.0,
#                 "content": content
#             } for content in retrieved_contents]
        
#         finally:
#             logging.info(f"{'='*50}\nLLM分析结束\n{'='*50}\n")
        
#     def _search_bm25(self, query: str, limit: int = 5) -> List[Dict]:
#         """
#         BM25检索
        
#         Args:
#             query: 查询文本
#             limit: 返回结果数量
            
#         Returns:
#             检索结果列表
#         """
#         # Tokenize查询文本
#         query_tokens = self._tokenize_text(query)
        
#         # 执行BM25检索
#         scores = self.bm25_index.get_scores(query_tokens)
        
#         # 获取top N的索引
#         top_n = np.argsort(-scores)[:limit]
        
#         # 获取对应的文档块
#         results = []
#         for idx in top_n:
#             chunk_idx = self.bm25_chunk_mapping[idx]
#             chunk = self.processed_chunks[chunk_idx]
#             results.append({
#                 "content": chunk["content"],
#                 "metadata": chunk["metadata"],
#                 "bm25_score": scores[idx]
#             })
        
#         return results
        
#     def _combine_search_results(self, vector_results: List[Dict], bm25_results: List[Dict], limit: int = 5) -> List[Dict]:
#         """
#         合并向量检索和BM25检索结果
        
#         Args:
#             vector_results: 向量检索结果
#             bm25_results: BM25检索结果
#             limit: 返回结果数量
            
#         Returns:
#             合并后的检索结果列表
#         """
#         # 合并结果
#         combined_results = []
        
#         # 处理向量检索结果
#         for result in vector_results:
#             combined_results.append({
#                 "content": result["content"],
#                 "metadata": result["metadata"],
#                 "semantic_score": result["score"],
#                 "bm25_score": 0.0
#             })
        
#         # 处理BM25检索结果
#         for result in bm25_results:
#             # 检查是否已存在相同内容的结果
#             existing = next((r for r in combined_results if r["content"] == result["content"]), None)
#             if existing:
#                 # 更新已存在的结果
#                 existing["bm25_score"] = result["bm25_score"]
#             else:
#                 # 添加新结果
#                 combined_results.append({
#                     "content": result["content"],
#                     "metadata": result["metadata"],
#                     "semantic_score": 0.0,
#                     "bm25_score": result["bm25_score"]
#                 })
        
#         # 按综合相似度排序（降序）
#         combined_results.sort(key=lambda x: x["semantic_score"] + x["bm25_score"], reverse=True)
        
#         # 返回top N的结果
#         return combined_results[:limit]
        
#     async def trace_content(self, content: str, limit: int = 5, min_score: float = 0.5, prompt: str = "", save_path: Optional[str] = None) -> List[Dict]:
#         """
#         溯源内容，查找最相似的文档块
        
#         Args:
#             content: 要溯源的内容
#             limit: 返回结果数量
#             min_score: 最小相似度阈值，只有大于此值的结果才会返回
#             prompt: 传递给LLM的提示词，用于判断检索内容与用户输入的相关性
#             save_path: 可选，若指定则将结果保存为JSON文件
        
#         Returns:
#             相似文档块列表，按相似度降序排列，包含LLM分析报告
#         """
#         # 确保文档已处理
#         if self.processed_chunks is None:
#             await self.process_document()
            
#         # 获取内容的嵌入向量
#         embedding = self.embeddings.get_embeddings([content])[0]
        
#         # 搜索相似文档，增加limit以获取更多结果用于过滤
#         search_limit = max(limit * 2, 10)  # 至少获取10个结果用于过滤
#         vector_results = self.vector_store.search(embedding, limit=search_limit)
#         logging.info(f"向量检索到 {len(vector_results)} 个结果")
        
#         # 执行BM25检索
#         bm25_results = self._search_bm25(content, limit=search_limit)
#         logging.info(f"BM25检索到 {len(bm25_results)} 个结果")
        
#         # 合并检索结果
#         combined_results = self._combine_search_results(vector_results, bm25_results, limit=search_limit)
#         logging.info(f"合并后共有 {len(combined_results)} 个检索结果")
        
#         # 收集所有检索内容
#         retrieved_contents = [result["content"] for result in combined_results]
        
#         # 异步批量调用LLM分析
#         logging.info(f"开始LLM分析，检索到 {len(retrieved_contents)} 个相关内容")
#         llm_analyses = await self._analyze_with_llm(content, retrieved_contents, prompt)
#         logging.info(f"LLM分析完成，获得 {len(llm_analyses)} 个分析结果")
        
#         # 合并结果
#         enhanced_results = []
#         logging.info(f"开始合并检索结果和LLM分析，共 {len(combined_results)} 个结果")
#         for idx, (result, analysis) in enumerate(zip(combined_results, llm_analyses)):
#             # 提取ICH条目编号
#             ich_numbers = result["metadata"].get("ich_item_numbers", [])
            
#             # 计算其他相似度指标
#             content_lower = content.lower()
#             result_content_lower = result["content"].lower()
            
#             # 关键词匹配
#             keywords = self._extract_keywords(content)
#             keyword_matches = sum(1 for kw in keywords if kw.lower() in result_content_lower)
#             keyword_score = keyword_matches / len(keywords) if keywords else 0
            
#             # 计算综合相似度（语义相似度占60%，BM25相似度占20%，关键词匹配占20%）
#             semantic_score = result.get("semantic_score", 0)
#             bm25_score = result.get("bm25_score", 0)
#             match_confidence = (semantic_score * 0.6 + bm25_score * 0.2 + keyword_score * 0.2)
            
#             # 只保留相似度大于阈值的
#             if match_confidence < min_score:
#                 logging.info(f"结果 {idx+1} 被过滤: 综合相似度 {match_confidence:.4f} < 阈值 {min_score}")
#                 continue
#             logging.info(f"结果 {idx+1} 被保留: 综合相似度 {match_confidence:.4f} >= 阈值 {min_score}")
                
#             # 增强结果
#             enhanced_result = {
#                 "content": result["content"],
#                 "metadata": result["metadata"],
#                 "semantic_score": semantic_score,
#                 "bm25_score": bm25_score,
#                 "keyword_score": keyword_score,
#                 "ich_numbers": ich_numbers,
#                 "match_confidence": match_confidence,
#                 "llm_analysis": analysis
#             }
#             enhanced_results.append(enhanced_result)
            
#             # 如果已经达到数量限制，提前退出
#             if len(enhanced_results) >= limit:
#                 break
                
#         # 按综合相似度排序（降序）
#         enhanced_results.sort(key=lambda x: x["match_confidence"], reverse=True)
        
#         # 保存为文件（如指定）
#         if save_path:
#             try:
#                 with open(save_path, "w", encoding="utf-8") as f:
#                     json.dump(enhanced_results, f, ensure_ascii=False, indent=2)
#                 logging.info(f"溯源结果已保存到: {save_path}")
#             except Exception as e:
#                 logging.error(f"保存溯源结果失败: {e}")
        
#         return enhanced_results
        
#     def _extract_keywords(self, text: str, min_length: int = 2) -> List[str]:
#         """
#         从文本中提取关键词
        
#         Args:
#             text: 输入文本
#             min_length: 最小词长度
            
#         Returns:
#             关键词列表
#         """
#         # 对中文文本使用jieba分词
#         if any('\u4e00' <= char <= '\u9fff' for char in text):  # 检测是否包含中文字符
#             words = list(jieba.cut(text))
#         else:
#             # 对英文文本使用正则表达式
#             words = re.findall(r'\b\w+\b', text)
        
#         # 过滤停用词和短词
#         stopwords = {"的", "了", "和", "是", "在", "有", "与", "为", "以", "及", "对", "上", "中", "下", 
#                     "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", 
#                     "be", "been", "being", "in", "on", "at", "to", "for", "with", "by",
#                     "about", "against", "between", "into", "through", "during", "before",
#                     "after", "above", "below", "from", "up", "down", "of", "off", "over",
#                     "under", "again", "further", "then", "once", "here", "there", "when",
#                     "where", "why", "how", "all", "any", "both", "each", "few", "more",
#                     "most", "other", "some", "such", "no", "nor", "not", "only", "own",
#                     "same", "so", "than", "too", "very", "can", "will", "just", "should",
#                     "now", "d", "ll", "m", "o", "re", "s", "t", "ve", "y", "ain", "aren",
#                     "couldn", "didn", "doesn", "hadn", "hasn", "haven", "isn", "ma",
#                     "mightn", "mustn", "needn", "shan", "shouldn", "wasn", "weren", "won"}
        
#         keywords = [word for word in words if len(word) >= min_length and word.lower() not in stopwords]
        
#         return keywords