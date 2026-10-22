# -*- coding: utf-8 -*-
"""生成《智能系统设计实践》课程报告 docx（≥20页，不含代码）"""
import os, json
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "figures")
SCREENS = os.path.join(ROOT, "runs", "screens")
RESULTS = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "docs", "智能系统设计与实践报告.docx")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

doc = Document()

# ---------- 页面设置 ----------
for sec in doc.sections:
    sec.top_margin = Cm(2.5); sec.bottom_margin = Cm(2.5)
    sec.left_margin = Cm(2.8); sec.right_margin = Cm(2.8)

# ---------- 样式 ----------
def set_font(style, ascii_font, east_font, size, bold=False, color=RGBColor(0, 0, 0)):
    style.font.name = ascii_font
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = color
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = OxmlElement('w:rFonts'); rpr.append(rfonts)
    rfonts.set(qn('w:eastAsia'), east_font)

st = doc.styles['Normal']
set_font(st, 'Times New Roman', '宋体', 12)
st.paragraph_format.line_spacing = 1.5
st.paragraph_format.space_after = Pt(0)

for name, size in (('Heading 1', 16), ('Heading 2', 14), ('Heading 3', 12.5)):
    hs = doc.styles[name]
    set_font(hs, 'Times New Roman', '黑体', size, bold=True)
    hs.paragraph_format.space_before = Pt(12)
    hs.paragraph_format.space_after = Pt(6)
    hs.paragraph_format.line_spacing = 1.3

def para(text, indent=True, bold=False, size=12, align=None, style=None, font='宋体'):
    p = doc.add_paragraph(style=style)
    p.paragraph_format.line_spacing = 1.5
    if indent:
        p.paragraph_format.first_line_indent = Pt(24)
    if align is not None:
        p.alignment = align
    r = p.add_run(text)
    r.bold = bold
    r.font.size = Pt(size)
    r.font.name = 'Times New Roman'
    r._element.rPr.rFonts.set(qn('w:eastAsia'), font)
    return p

def h1(t): doc.add_heading(t, level=1)
def h2(t): doc.add_heading(t, level=2)

def pic(path, caption=None, width=15.5):
    if not os.path.exists(path):
        print("MISSING FIG:", path); return
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(path, width=Cm(width))
    if caption:
        c = doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraph_format.space_after = Pt(10)
        r = c.add_run(caption); r.font.size = Pt(10.5); r.bold = False
        r.font.name = 'Times New Roman'
        r._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

def table(headers, rows, widths=None, fontsize=10.5):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, htext in enumerate(headers):
        cell = t.rows[0].cells[j]
        cell.text = ''
        r = cell.paragraphs[0].add_run(htext)
        r.bold = True; r.font.size = Pt(fontsize)
        r.font.name = 'Times New Roman'
        r._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.rows[i + 1].cells[j]
            cell.text = ''
            r = cell.paragraphs[0].add_run(str(val))
            r.font.size = Pt(fontsize)
            r.font.name = 'Times New Roman'
            r._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    if widths:
        for j, w in enumerate(widths):
            for row in t.rows:
                row.cells[j].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return t

def page_break():
    doc.add_page_break()

# ---------- 读取真实实验结果 ----------
summary = {}
sf = os.path.join(RESULTS, "summary.json")
if os.path.exists(sf):
    summary = json.load(open(sf, encoding="utf-8"))

def worst_best(model):
    rec = summary.get(model, {})
    pc = rec.get("per_class", {})
    if not pc:
        return [], []
    items = sorted(pc.items(), key=lambda kv: kv[1]["recall"])
    return items[:5], items[-5:]

# ================= 封面 =================
for _ in range(4):
    doc.add_paragraph()
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('《智能系统设计实践》报告'); r.bold = True; r.font.size = Pt(26)
r.font.name = 'Times New Roman'; r._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
doc.add_paragraph()
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('基于深度学习的图像分类识别系统的设计与实现\n——以花卉 102 类细粒度分类为例')
r.bold = True; r.font.size = Pt(18)
r.font.name = 'Times New Roman'; r._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
for _ in range(6):
    doc.add_paragraph()
info = [
    ('学    院', '电子与信息工程学院'),
    ('专    业', '计算机科学与技术'),
    ('班    级', ''),
    ('学    号', ''),
    ('姓    名', '闫洪杰（组长）  钱雪  聂晓丽'),
    ('指导老师', '曾昭武'),
    ('时    间', '2026/10/20 - 2026/10/29'),
]
for k, v in info:
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f'{k}：    {v}'); r.font.size = Pt(14)
    r.font.name = 'Times New Roman'; r._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
page_break()

# ================= 摘要 =================
h1('摘  要')
para('图像分类与识别是计算机视觉领域最基础、应用最广泛的任务之一。随着深度学习技术的快速发展，'
     '基于卷积神经网络的图像分类系统在准确率上已经超越了传统人工特征方法，并在花卉识别、植物科普、'
     '智慧农业等场景中展现出重要的应用价值。本文设计并实现了一个基于深度学习的图像分类与识别系统：'
     '系统以 Oxford 102 Category Flower 数据集（102 类、共 8189 张图像）为基础构建微调数据集，'
     '按 6:2:2 的比例分层划分为训练集、验证集与测试集；在 ImageNet 预训练权重的基础上，采用'
     '两阶段迁移学习策略分别微调 ResNet18、ResNet34、MobileNetV3-Large 与 EfficientNet-B0 四种'
     '深度模型，使模型适应花卉细粒度分类任务。', indent=True)
para('在系统实现方面，本文基于 Flask 框架与 PyTorch 搭建了完整的前后端系统：前端页面支持用户'
     '上传图像、选择不同深度模型并获得 Top-5 识别结果；后端管理模块实现了模型训练与微调任务的'
     '在线调度、识别记录的持久化存储以及图像深度特征的提取与存储。实验结果表明，四种模型在测试集'
     '上的 Top-1 准确率均达到 90% 以上，其中 EfficientNet-B0 达到 {:.2f}%。'.format(
     summary.get("efficientnet_b0", {}).get("top1", 0) * 100), indent=True)
para('本文还利用准确率、混淆矩阵、类别精确率/召回率等指标对模型性能进行了深入分析，讨论了模型'
     '对不同花卉类别的敏感性与易混淆模式，并对不同模型的精度与推理效率进行了对比。最后，论文对'
     '系统的不足与改进方向进行了总结和展望。', indent=True)
para('关键词：图像分类；迁移学习；卷积神经网络；Flask；混淆矩阵', indent=False, bold=True)
page_break()

# ================= 目录 =================
h1('目  录')
toc = [('摘  要', 2), ('0 引言', 4), ('1 系统总体设计', 5), ('2 数据集构建', 8),
       ('3 模型设计与训练', 11), ('4 系统实现', 13), ('5 系统页面展示', 16),
       ('6 实验结果与分析', 23), ('7 结论', 29), ('参考文献', 30), ('附录A 提交材料与运行说明', 31)]
for name, pg in toc:
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.8
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(15.2), 2)  # 右对齐制表位
    r = p.add_run(name)
    r.font.size = Pt(12); r.font.name = 'Times New Roman'
    r._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    r2 = p.add_run('\t' + str(pg))
    r2.font.size = Pt(12); r2.font.name = 'Times New Roman'
    r2._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
page_break()

# ================= 0 引言 =================
h1('0 引言')
para('随着智能手机和数码相机的普及，人们每天都会产生海量的图像数据。如何让计算机像人类一样'
     '“看懂”图像，一直是人工智能领域的核心问题之一。图像分类任务要求计算机对输入的图像给出'
     '所属类别的判断，是目标检测、图像分割、图像检索等更复杂视觉任务的基础。传统方法依赖人工'
     '设计的特征（如 SIFT、HOG 等）配合支持向量机等分类器，特征表达能力有限。自 2012 年'
     'AlexNet 在 ImageNet 大规模视觉识别挑战赛（ILSVRC）上取得突破以来，以卷积神经网络'
     '（Convolutional Neural Network, CNN）为代表的深度学习方法成为图像分类的主流技术路线，'
     '并在识别精度上不断刷新纪录。', indent=True)
para('然而，从头训练一个高性能的深度模型通常需要百万级规模的标注数据和昂贵的计算资源。对于'
     '校园级课程实践而言，更可行的做法是“迁移学习”：先在 ImageNet 等大规模数据集上预训练'
     '模型，使卷积层获得通用的底层视觉表示能力，再在目标任务的小规模数据集上对网络进行微调'
     '（Fine-tuning）。实践表明，这种策略只需数千张图像即可在细分任务上取得优异的识别效果。'
     '花卉识别是一个典型的小样本细粒度分类场景：不同品种的花卉外观差异细微，类间相似度高，'
     '适合用来检验迁移学习策略和模型设计。', indent=True)
para('本课程设计按照《智能系统设计与实践》课程要求，完成以下工作：（1）构建一个微调数据集，'
     '图像类别不少于 20 类、总图像不少于 2000 张，并按 6:2:2 划分训练集、验证集与测试集；'
     '（2）搭建前端页面，支持用户上传图像、选择不同深度模型进行分类识别并展示结果；'
     '（3）实现后端管理，包括深度模型的训练与微调、图像特征的存储、识别结果的记录与存储；'
     '（4）对深度模型的性能进行分析，通过准确率、混淆矩阵等指标讨论模型对不同类别的敏感度与'
     '针对性；（5）撰写设计与实践报告。', indent=True)
para('本文采用 Oxford 102 Category Flower 数据集（102 类，8189 张），在其上微调四种经典深度'
     '模型（ResNet18、ResNet34、MobileNetV3-Large、EfficientNet-B0），构建了完整的前后端识别'
     '系统，并对模型性能进行了系统的对比分析。全文结构安排如下：第 1 章介绍系统总体设计；'
     '第 2 章介绍数据集的构建过程；第 3 章介绍模型设计与训练细节；第 4 章介绍系统实现；'
     '第 5 章展示系统页面；第 6 章给出实验结果与分析；第 7 章总结全文。', indent=True)
page_break()

# ================= 1 系统总体设计 =================
h1('1 系统总体设计')
h2('1.1 设计目标与需求分析')
para('按照课程要求，本系统需要同时满足“前端识别”与“后端管理”两方面的功能需求，并配套完成'
     '数据、实验与报告工作。具体需求归纳如下：', indent=True)
table(['编号', '需求类型', '需求描述'],
      [['R1', '前端-上传', '用户可通过点击或拖拽方式上传待识别图像，页面实时预览'],
       ['R2', '前端-模型选择', '提供多种深度模型供用户选择，展示各模型指标'],
       ['R3', '前端-结果展示', '给出 Top-5 类别及其 Softmax 概率的可视化展示'],
       ['R4', '前端-历史', '展示历史识别记录（图像、结果、模型、时间）'],
       ['R5', '后端-训练', '支持深度模型的训练与微调，可在线发起并查看日志'],
       ['R6', '后端-特征存储', '对上传图像提取深度特征向量并持久化存储'],
       ['R7', '后端-记录存储', '识别结果（含图像与置信度）持久化存储，可查询'],
       ['R8', '数据集', '类别数≥20，图像总数≥2000，按 6:2:2 划分三个集合'],
       ['R9', '结果分析', '准确率、混淆矩阵等指标分析，图表齐全'],
       ['R10', '文档', '撰写不少于 20 页的设计与实践报告']],
      widths=[1.6, 3.2, 11.6])
h2('1.2 总体架构')
para('系统采用浏览器/服务器（B/S）架构，自上而下分为表现层、服务层与数据层，如图 1-1 所示。'
     '表现层为浏览器中的前端页面（HTML/CSS/JavaScript），承担图像上传、模型选择与结果展示等'
     '交互功能；服务层由 Flask 应用与 PyTorch 推理引擎组成，负责接收请求、图像预处理、深度'
     '模型推理、特征提取以及训练任务的调度；数据层使用文件系统与 SQLite 数据库，分别保存上传'
     '图像、模型权重、训练日志以及结构化业务数据（识别记录、特征向量、训练任务）。各层之间'
     '通过 RESTful API 通信，前后端解耦，便于独立开发与维护。', indent=True)
pic(os.path.join(FIG, "architecture.png"), '图 1-1  系统总体架构', 15.5)
h2('1.3 技术选型')
para('系统开发环境为 macOS（Apple M5 芯片），推理与训练均借助 PyTorch 的 MPS 后端进行硬件'
     '加速。主要技术选型及理由如表 1-2 所示。', indent=True)
table(['技术', '用途', '选型理由'],
      [['Python 3.11', '主要开发语言', '生态成熟，深度学习框架支持完善'],
       ['PyTorch / torchvision', '模型构建、训练与推理', '动态图易调试，内置 ImageNet 预训练权重，支持 MPS 加速'],
       ['Flask', '后端 Web 框架', '轻量、简单，适合中小型课程项目，便于扩展 REST API'],
       ['SQLite', '业务数据持久化', '零配置、单文件，满足识别记录与特征存储需求'],
       ['HTML/CSS/JavaScript', '前端页面', '原生实现，无需前端构建链，交互流畅'],
       ['Matplotlib / scikit-learn', '评估指标与图表', '科学绘图与指标计算的标准工具'],
       ['Playwright', '自动化演示与截图', '可录制浏览器操作生成演示视频']],
      widths=[4.2, 4.6, 7.6])
h2('1.4 功能模块划分')
para('系统按功能划分为六个模块：', indent=True)
table(['模块', '主要职责'],
      [['图像上传模块', '接收前端上传图像，校验格式并统一存储'],
       ['模型推理模块', '加载模型注册表，完成预处理、前向推理、Softmax 归一化与特征提取'],
       ['识别记录模块', '将每次识别结果（原图、Top-5、置信度、模型、时间）写入数据库'],
       ['特征存储模块', '通过前向 hook 截取分类层之前的深度特征向量并持久化'],
       ['训练管理模块', '以后台线程方式运行训练脚本，记录日志并在完成后自动重载模型'],
       ['管理后台模块', '展示数据集概况、模型指标、识别记录、特征统计与训练任务状态']],
      widths=[4.5, 11.9])
h2('1.5 系统工作流程')
para('一次完整的识别流程为：用户在浏览器选择图像并上传；前端将图像与所选模型名以 multipart'
     '表单提交至 /api/classify 接口；后端将图像缩放并中心裁剪为 224×224，按 ImageNet 均值'
     '与标准差归一化后送入对应模型；模型输出 102 维 logits，经 Softmax 得到类别概率分布，'
     '取概率最高的 5 个类别作为结果；同时通过 hook 提取分类层之前的深度特征向量；随后后端将'
     '原图保存至 uploads 目录，将识别记录与特征向量写入 SQLite 数据库，并将 Top-5 结果以'
     'JSON 返回前端渲染。训练流程则由管理员在后台发起：后端启动后台线程执行训练脚本，训练'
     '日志实时写入数据库供前端轮询展示，训练结束后自动重载模型注册表。', indent=True)
h2('1.6 小组分工')
para('本小组共 3 人，分工如表 1-4 所示。组长闫洪杰承担总体设计、数据集构建、模型训练与结果'
     '分析等核心任务，并负责报告撰写与整合。', indent=True)
table(['成员', '承担工作'],
      [['闫洪杰（组长）', '系统总体架构设计；数据集构建与预处理；四种深度模型的训练与微调实验；\n模型性能评估与结果分析（准确率、混淆矩阵、类别敏感度）；报告主要章节撰写与整合'],
       ['钱雪', '后端开发：Flask 服务与 REST 接口；识别记录与特征向量的存储设计（SQLite）；\n训练管理模块与模型注册表实现；后端联调与数据库维护'],
       ['聂晓丽', '前端开发：上传与识别页面、结果可视化、历史记录页面；后台管理界面；\n系统功能测试；系统演示视频制作与材料整理']],
      widths=[3.6, 12.8], fontsize=10)
page_break()

# ================= 2 数据集构建 =================
h1('2 数据集构建')
h2('2.1 数据集简介')
para('实验采用牛津大学视觉几何组（VGG）公开的 Oxford 102 Category Flower 数据集。该数据集'
     '包含英国常见的 102 个花卉类别，共 8189 张自然场景下拍摄的花卉图像，图像分辨率不统一，'
     '同一类别内花卉的姿态、光照、尺度差异较大，且不同类别之间存在外观相似的情况，是经典的'
     '细粒度图像分类基准，非常契合本课程对“构建微调数据集”的要求。数据集的类别数（102 类）'
     '远超课程要求的 20 类，图像总数（8189 张）远超要求的 2000 张，为微调实验提供了充足的'
     '数据基础。', indent=True)
h2('2.2 数据下载与整理')
para('数据集从 VGG 官方站点下载（https://www.robots.ox.ac.uk/~vgg/data/flowers/102/），'
     '共包含图像压缩包 102flowers.tgz（约 329MB，解压后为 jpg 目录下 8189 张图像）与标签'
     '文件 imagelabels.mat。通过 Python 脚本读取 imagelabels.mat 获得每张图像对应的类别'
     '编号（1~102），并将官方类别名称与编号一一对应，生成带语义类别名的目录结构：'
     'data/flower102/{train,val,test}/{类别名}/*.jpg，便于 torchvision 的 ImageFolder '
     '直接加载。', indent=True)
h2('2.3 类别与规模统计')
para('数据集共 102 个类别，各类别的图像数量从 40 张到 258 张不等，属于典型的不平衡细粒度'
     '数据集。各类别图像数量分布与总体划分比例如图 2-1 所示。', indent=True)
pic(os.path.join(FIG, "dataset_dist.png"), '图 2-1  各类别图像数量分布（左）与 6:2:2 数据集划分（右）', 16.5)
h2('2.4 6:2:2 分层划分')
_ds = json.load(open(os.path.join(ROOT, "data", "flower102_stats.json"), encoding="utf-8")) if os.path.exists(os.path.join(ROOT, "data", "flower102_stats.json")) else {"split":{"train":0,"val":0,"test":0},"total":8189}
_SP = _ds["split"]
para(f'课程要求按 6:2:2 划分训练集、验证集与测试集。为避免随机划分造成类别比例失衡，本文'
     f'采用按类别分层的随机划分策略：先按类别标签分组，再在每一类别内部以固定随机种子'
     f'（seed=42）按 60%:20%:20% 划分，保证每个类别在三个子集中都具有相同的比例。最终得到'
     f'训练集 {_SP["train"]} 张、验证集 {_SP["val"]} 张、测试集 {_SP["test"]} 张，如表 2-1 所示。划分结果连同类别信息'
     f'一起保存为 JSON 文件，保证实验可复现。', indent=True)
table(['子集', '图像数量', '占比', '用途'],
      [['训练集（train）', str(_SP["train"]), '%.1f%%' % (_SP["train"] / _ds["total"] * 100), '模型微调训练'],
       ['验证集（val）', str(_SP["val"]), '%.1f%%' % (_SP["val"] / _ds["total"] * 100), '超参数调整、早停与最优模型选择'],
       ['测试集（test）', str(_SP["test"]), '%.1f%%' % (_SP["test"] / _ds["total"] * 100), '最终性能评估，仅在评估阶段使用'],
       ['合计', str(_ds["total"]), '100%', '——']],
      widths=[4.5, 3.5, 3.0, 5.4])
h2('2.5 数据预处理与增强')
para('训练阶段采用随机裁剪增强（RandomResizedCrop，缩放范围为 0.6~1.0）、随机水平翻转与'
     '轻微颜色抖动（ColorJitter），以增强模型对尺度与光照变化的鲁棒性，缓解小数据集上的过'
     '拟合；随后统一变换为 224×224 的 RGB 张量，并按 ImageNet 统计量（均值 [0.485,0.456,'
     '0.406]，标准差 [0.229,0.224,0.225]）归一化。验证集与测试集则采用确定性预处理：等比'
     '缩放至 256 像素后中心裁剪 224×224，再作相同归一化，保证评估的公平性。', indent=True)
h2('2.6 数据示例')
para('图 2-2 展示了 25 个类别的示例图像，可以看到不同类别花卉在形态、颜色与纹理上的差异，'
     '以及部分类别之间的高度相似性，这也预示了后续混淆矩阵分析中部分类别容易相互误分的现象。', indent=True)
pic(os.path.join(FIG, "dataset_samples.png"), '图 2-2  数据集示例（25 个类别随机各取 1 张训练图像）', 15.5)
page_break()

# ================= 3 模型设计与训练 =================
h1('3 模型设计与训练')
h2('3.1 模型选择')
para('为了满足“前端可选择不同深度模型”的课程要求，同时也为了对比不同结构深度模型的性能，'
     '本文选择了四种具有代表性的卷积网络：ResNet18 与 ResNet34 采用残差连接解决深层网络'
     '退化问题，结构简单、训练稳定；MobileNetV3-Large 使用深度可分离卷积与神经结构搜索'
     '（NAS）得到的轻量结构，适合端侧部署；EfficientNet-B0 通过复合缩放（Compound Scaling）'
     '在深度、宽度与分辨率三个维度上均衡扩展网络，参数量小且精度高。四个模型在 ImageNet 上'
     '的 Top-1 准确率与参数量差异明显，覆盖了“轻量高效—深度高精度”的完整谱系，便于后续的'
     '精度与效率对比分析。', indent=True)
table(['模型', '结构特点', '参数量(约)', 'ImageNet Top-1(约)'],
      [['ResNet18', '18 层残差网络', '11.2M', '69.8%'],
       ['ResNet34', '34 层残差网络', '21.3M', '73.3%'],
       ['MobileNetV3-Large', 'NAS 搜索的轻量网络，深度可分离卷积', '5.5M', '75.2%'],
       ['EfficientNet-B0', '复合缩放的均衡网络', '5.3M', '77.1%']],
      widths=[4.2, 6.4, 2.6, 3.2])
h2('3.2 迁移学习与微调策略')
para('四种模型均加载 torchvision 提供的 ImageNet-1K 预训练权重，将最后的全连接分类层替换'
     '为输出维度 102 的新分类层（ResNet 替换 fc 层，MobileNetV3 与 EfficientNet 替换'
     'classifier 的最后一层）。由于预训练权重已具备通用的底层视觉特征提取能力，微调时采用'
     '两阶段策略：第一阶段冻结骨干网络全部参数，仅以 3×10⁻⁴ 的学习率训练新分类头，使随机'
     '初始化的分类头快速收敛；第二阶段解冻全部参数，以 1×10⁻⁴ 的学习率对整网进行精细微调，'
     '让底层特征也逐步适应花卉域。损失函数采用带标签平滑（label smoothing=0.1）的交叉熵，'
     '以缓解过拟合、提升泛化能力；优化器使用 AdamW（weight decay=1×10⁻⁴），并配合'
     'ReduceLROnPlateau 学习率调度器，在验证集准确率连续两个 epoch 不提升时将学习率减半。'
     '训练在 Apple M5 的 MPS 后端上进行，前向与反向过程使用 FP16 混合精度加速。', indent=True)
h2('3.3 训练配置')
table(['配置项', '取值'],
      [['输入分辨率', '224×224'],
       ['批次大小', '32'],
       ['训练轮数', '15（前 3 轮仅训练分类头）'],
       ['优化器 / 学习率', 'AdamW / 头 3×10⁻⁴，整网 1×10⁻⁴'],
       ['学习率调度', 'ReduceLROnPlateau（patience=2，factor=0.5）'],
       ['损失函数', '交叉熵 + 标签平滑 0.1'],
       ['数据增强', '随机裁剪、水平翻转、颜色抖动'],
       ['混合精度', 'MPS 后端 FP16 autocast'],
       ['最优模型选择', '按验证集准确率保存最优权重']],
      widths=[5.2, 11.2])
h2('3.4 训练过程与曲线')
para('四个模型均训练 15 个 epoch，训练损失与验证集准确率曲线如图 3-1 所示。可以看到，得益于'
     'ImageNet 预训练权重与两阶段微调策略，各模型在第 1 个 epoch 的验证准确率即超过 70%，'
     '随后迅速收敛：验证准确率在前 5 个 epoch 内快速上升，之后进入平缓爬升阶段；训练损失'
     '单调下降并趋于稳定。ResNet34 与 EfficientNet-B0 的最终验证准确率高于两个轻量模型，'
     '说明更深的网络结构在细粒度分类任务上具有更强的特征表达能力。', indent=True)
pic(os.path.join(FIG, "training_curves.png"), '图 3-1  四模型训练损失曲线（左）与验证集准确率曲线（右）', 16.0)
para('各模型训练过程的详细数值记录保存在 runs/ 目录的 JSON 日志中，供报告与管理后台查看。', indent=True)
page_break()

# ================= 4 系统实现 =================
h1('4 系统实现')
h2('4.1 后端服务与接口设计')
para('后端基于 Flask 实现，启动时自动扫描 models 目录加载全部可用模型，构建“模型注册表”。'
     '注册表中保存模型实例、类别名列表与评估指标，推理请求按名称直接索引对应模型，模型切换'
     '开销为零。核心接口设计如表 4-1 所示。', indent=True)
table(['方法', '路径', '功能说明'],
      [['GET', '/', '识别台前端页面'],
       ['GET', '/admin', '后台管理页面'],
       ['GET', '/api/models', '返回已加载模型列表及评估指标'],
       ['POST', '/api/classify', '上传图像+模型名，返回 Top-5 结果并持久化记录与特征'],
       ['GET', '/api/records', '分页查询识别记录，支持按模型筛选'],
       ['GET', '/api/record/<id>', '查询单条记录详情（含特征向量）'],
       ['GET', '/api/stats', '识别/特征统计数据与数据集概况'],
       ['POST', '/api/train', '发起后台训练任务（模型+轮数）'],
       ['GET', '/api/train_jobs', '查询训练任务列表与日志'],
       ['GET', '/api/health', '服务健康检查']],
      widths=[2.2, 4.4, 9.8])
h2('4.2 特征存储设计')
para('“特征存储”是本课程的一项明确要求。系统在每次识别时，除输出类别概率外，还通过注册前向'
     'hook 的方式截取模型分类层之前的深度特征向量：对 ResNet 系列取全局平均池化后的 512 维'
     '向量；对 MobileNetV3-Large 取 960 维向量；对 EfficientNet-B0 取 1280 维向量。特征向量'
     '保留 4 位小数后以 JSON 数组形式写入 SQLite 的 features 表，并与识别记录通过外键关联。'
     '这些特征可作为图像的高层语义表示，为后续的相似图像检索、特征复用与进一步分析提供基础。', indent=True)
h2('4.3 识别记录存储设计')
para('每次识别结束后，系统将原图保存至 uploads 目录，并在数据库 records 表中写入一条记录，'
     '包含原文件名、存储路径、所用模型、Top-1 类别与置信度、Top-5 完整结果（JSON）、图像'
     '尺寸与识别时间。数据库共包含三张表：records（识别记录）、features（特征向量）与'
     'train_jobs（训练任务），表结构如表 4-2 所示。SQLite 单文件数据库零配置、易迁移，'
     '完全满足课程项目的持久化需求。', indent=True)
table(['表名', '主要字段', '说明'],
      [['records', 'id, filename, stored_path, model, top1, top1_prob, top5, image_size, created_at', '识别记录：结果与图像路径'],
       ['features', 'id, record_id, model, dim, vector', '深度特征向量（JSON 数组，含维数）'],
       ['train_jobs', 'id, model, epochs, status, log, best_val_acc, started_at, finished_at', '训练任务：状态、实时日志与最优验证准确率']],
      widths=[2.6, 8.6, 5.2], fontsize=9.5)
h2('4.4 训练管理模块')
para('管理后台可在线发起训练任务：前端提交模型名与训练轮数后，后端以守护线程启动训练脚本，'
     '脚本的输出流逐行写入 train_jobs 表，前端每 2.5 秒轮询刷新日志，实现训练过程的实时'
     '可视化；任务结束后自动记录最优验证准确率并重新加载模型注册表，新模型即刻可被前端选择。'
     '该模块使“模型训练与微调”成为系统的一项可操作功能，而非仅停留在离线脚本层面。', indent=True)
h2('4.5 前端页面实现')
para('识别台页面由上传区、模型选择区、结果展示区与历史记录区组成。上传区支持点击选择与'
     '拖拽上传，并通过 URL.createObjectURL 实现本地预览；模型选择区以卡片形式展示各模型的'
     '测试集准确率、参数量与推理耗时，帮助用户比较选择；结果区将 Top-5 类别按 Softmax 概率'
     '绘制为横向概率条，概率最高的类别以高亮渐变显示；历史记录区以缩略图网格展示最近的识别'
     '记录。管理后台页面包括统计卡片、数据集概况、训练面板与识别记录表格四部分，采用轮询'
     '机制保持数据与训练日志的实时更新。整体界面为深色主题，适配桌面浏览器。', indent=True)
h2('4.6 项目目录结构')
para('项目代码目录结构如图 4-1 所示（报告中省略具体代码，完整源码随系统一并提交）。', indent=True)
pic(os.path.join(FIG, "structure.png"), '图 4-1  项目目录结构', 11.5)
page_break()

# ================= 5 系统页面展示 =================
h1('5 系统页面展示')
para('系统在本地启动后（python app/app.py，端口 8000），通过浏览器访问。以下通过自动化工具'
     'Playwright 截取系统运行时的真实页面。', indent=True)
para('识别台初始页面如图 5-1 所示：顶部为导航栏，左侧为拖拽上传区，下方为四种模型的卡片'
     '选择区（展示各模型测试集 Top-1 准确率、参数量与单张推理耗时）。', indent=True)
pic(os.path.join(SCREENS, "01_index_initial.png"), '图 5-1  识别台初始页面', 15.5)
para('用户上传一张玫瑰图像后，页面实时预览，如图 5-2 所示。', indent=True)
pic(os.path.join(SCREENS, "02_uploaded.png"), '图 5-2  图像上传与预览', 15.5)
para('选择 ResNet18 模型点击“开始识别”，系统给出 Top-5 识别结果与概率分布，最高概率类别'
     '“rose”以高亮显示，同时页面上方展示记录编号与推理耗时，如图 5-3 所示。', indent=True)
pic(os.path.join(SCREENS, "03_result_resnet18.png"), '图 5-3  ResNet18 识别结果（玫瑰，置信度 99%+）', 15.5)
para('切换至 EfficientNet-B0 模型对向日葵图像进行识别，结果如图 5-4 所示，可以看到不同模型'
     '对同一类别的置信度分布存在差异。', indent=True)
pic(os.path.join(SCREENS, "04_result_efficientnet.png"), '图 5-4  切换 EfficientNet-B0 识别向日葵', 15.5)
para('识别历史记录以缩略图网格展示，如图 5-5 所示。', indent=True)
pic(os.path.join(SCREENS, "05_history.png"), '图 5-5  识别历史记录区', 15.5)
para('管理后台如图 5-6、图 5-7 所示：顶部统计卡片展示数据集规模、模型数、识别与特征统计；'
     '训练面板可发起在线微调并实时查看日志；识别记录表格展示每次识别的完整信息，包括特征'
     '向量维数，体现了“特征存储”与“识别结果记录”两项课程要求。', indent=True)
pic(os.path.join(SCREENS, "06_admin_top.png"), '图 5-6  管理后台（统计卡片、数据集概况与训练面板）', 15.5)
pic(os.path.join(SCREENS, "07_admin_records.png"), '图 5-7  管理后台（识别记录与特征存储）', 15.5)
page_break()

# ================= 6 实验结果与分析 =================
h1('6 实验结果与分析')
h2('6.1 评估指标')
para('在测试集（1638 张，模型训练全程未参与）上对四个模型进行评估，采用以下指标：Top-1 与'
     'Top-5 准确率衡量整体分类能力；类别精确率、召回率与 F1 值衡量模型对每个类别的敏感度；'
     '混淆矩阵展示每个真实类别被预测为各预测类别的样本分布，用于分析类别间易混淆模式；同时'
     '统计参数量与单张图像平均推理耗时（MPS 后端）作为效率指标。', indent=True)
h2('6.2 总体性能')
table(['模型', 'Top-1 准确率', 'Top-5 准确率', '验证集最优', '参数量(M)', '单张推理(ms)'],
      [[m, f"{r['top1']*100:.2f}%", f"{r['top5']*100:.2f}%", f"{r['val_acc']*100:.2f}%",
        r['params_M'], f"{r['infer_ms']:.1f}"] for m, r in summary.items()],
      widths=[3.6, 2.8, 2.8, 2.8, 2.4, 2.8])
para('由表 6-1 可见，四种模型测试集 Top-1 准确率均超过 90%，Top-5 准确率均超过 99%，验证了'
     '迁移学习策略在花卉细粒度分类任务上的有效性。EfficientNet-B0 与 ResNet34 精度最高，'
     '轻量模型 MobileNetV3-Large 的参数量与推理耗时最低，展现出良好的精度-效率折中。', indent=True)
h2('6.3 混淆矩阵分析')
para('图 6-1 为 ResNet18 与 EfficientNet-B0 在测试集上的混淆矩阵（102×102）。矩阵对角线'
     '高亮，说明绝大多数样本被正确分类；非对角元素整体稀疏，错分样本集中于少数外观相似的'
     '类别对之间，例如“pink primrose”与“balloon flower”、“thorn apple”与“petunia”等'
     '花色、花型相近的类别，反映出细粒度分类中类间相似性带来的固有困难。', indent=True)
pic(os.path.join(FIG, "cm_resnet18.png"), '图 6-1(a)  ResNet18 测试集混淆矩阵', 15.5)
pic(os.path.join(FIG, "cm_efficientnet_b0.png"), '图 6-1(b)  EfficientNet-B0 测试集混淆矩阵', 15.5)
h2('6.4 类别敏感度分析')
para('为进一步考察模型对不同类别的敏感度，按类别准确率排序，图 6-2 给出各模型准确率最低与'
     '最高的 20 个类别。整体上数据量大、外观特征明显的类别（如 sunflower、rose、daisy 等）'
     '识别准确率高；而图像数量少、类间高度相似或外观变异大的类别（如部分兰花、秋海棠类）'
     '准确率较低，说明类别敏感度与数据规模、类内变异度密切相关。', indent=True)
pic(os.path.join(FIG, "class_acc_resnet18.png"), '图 6-2(a)  ResNet18 各类别准确率（最低/最高 20 类）', 15.5)
pic(os.path.join(FIG, "class_acc_efficientnet_b0.png"), '图 6-2(b)  EfficientNet-B0 各类别准确率（最低/最高 20 类）', 15.5)
h2('6.5 模型对比分析')
pic(os.path.join(FIG, "model_compare.png"), '图 6-3  模型精度、参数量与推理耗时对比', 15.5)
para('图 6-3 从准确率、参数量与推理耗时三个维度对比四个模型。EfficientNet-B0 以约 5.3M 的'
     '参数量取得与 ResNet34 相当甚至更优的准确率，体现了复合缩放结构的效率优势；ResNet 系列'
     '虽然参数量更大，但结构简单、训练稳定；MobileNetV3-Large 以最小的推理耗时保持 90% 以上'
     '的准确率，适合资源受限的部署场景。综合来看，若追求最高精度可选用 EfficientNet-B0 或'
     'ResNet34；若面向移动端或实时场景，MobileNetV3-Large 是更均衡的选择。', indent=True)
h2('6.6 识别样例展示')
para('图 6-4 展示了 ResNet18 在测试集上的识别样例，上排为正确识别样例（含置信度），下排为'
     '错误样例。错误样例的预测类别与真实类别往往外观相近，且错误预测的置信度普遍偏低，说明'
     '模型在不确定时输出更加分散的概率分布，这一性质可用于后续的拒识或人工复核机制。', indent=True)
pic(os.path.join(FIG, "samples_resnet18.png"), '图 6-4  ResNet18 识别样例（上：正确，下：错误）', 16.0)
h2('6.7 结果讨论')
para('综合以上分析可以得出三点结论。第一，迁移学习有效：仅用约 5000 张训练图像即可将'
     'ImageNet 预训练模型微调至 90% 以上的花卉识别准确率，说明预训练特征具有良好的可迁移'
     '性。第二，类别敏感度不均衡：模型对数据充足、特征鲜明的类别敏感，对数据稀疏或类间相似'
     '的类别敏感度下降，混淆矩阵显示错分具有聚集性，未来可通过针对性数据扩充、难例挖掘与'
     '度量学习进一步改善。第三，精度与效率存在权衡：不同结构的模型在准确率、参数量与推理'
     '耗时上各有侧重，系统支持在线切换模型，用户可按需选择。', indent=True)
page_break()

# ================= 7 结论 =================
h1('7 结论')
para('本文按照《智能系统设计与实践》课程要求，完成了一个基于深度学习的图像分类与识别系统。'
     '在数据方面，基于 Oxford 102 Category Flower 数据集构建了 102 类、共 8189 张图像的'
     '微调数据集，并按 6:2:2 分层划分训练集、验证集与测试集；在模型方面，采用两阶段迁移学习'
     '策略微调了 ResNet18、ResNet34、MobileNetV3-Large 与 EfficientNet-B0 四种深度模型；'
     '在系统方面，基于 Flask 与 PyTorch 实现了前端识别页面与后端管理模块，支持图像上传、'
     '多模型选择、Top-5 结果展示、在线训练与微调、识别记录存储与深度特征存储；在分析方面，'
     '利用准确率、混淆矩阵与类别指标对模型性能进行了系统分析。实验表明，四种模型测试集 '
     'Top-1 准确率均超过 90%，系统功能完整、运行稳定，达到了课程设计目标。', indent=True)
para('本工作仍存在可改进之处：一是数据集存在类别不平衡，可引入重加权采样与数据扩充；二是'
     '混淆矩阵显示部分相似类别之间仍有误分，可引入注意力机制或度量学习；三是系统目前为单机'
     '部署，后续可扩展为多用户并发服务并增加图像检索等特征应用功能。总体而言，通过本次课程'
     '实践，小组成员完整经历了“需求分析—数据构建—模型训练—系统开发—性能评估”的智能系统'
     '设计全流程，加深了对深度学习工程实践的理解。', indent=True)
page_break()

# ================= 参考文献 =================
h1('参考文献')
refs = [
    'He K, Zhang X, Ren S, et al. Deep Residual Learning for Image Recognition[C]. CVPR, 2016: 770-778.',
    'Sandler M, Howard A, Zhu M, et al. MobileNetV2: Inverted Residuals and Linear Bottlenecks[C]. CVPR, 2018: 4510-4520.',
    'Howard A, Sandler M, Chu G, et al. Searching for MobileNetV3[C]. ICCV, 2019: 1314-1324.',
    'Tan M, Le Q V. EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks[C]. ICML, 2019: 6105-6114.',
    'Huang G, Liu Z, van der Maaten L, et al. Densely Connected Convolutional Networks[C]. CVPR, 2017: 4700-4708.',
    'Krizhevsky A, Sutskever I, Hinton G E. ImageNet Classification with Deep Convolutional Neural Networks[C]. NIPS, 2012: 1097-1105.',
    'Nilsback M E, Zisserman A. Automated Flower Classification over a Large Number of Classes[C]. ICVGIP, 2008: 722-729.',
    'Pan S J, Yang Q. A Survey on Transfer Learning[J]. IEEE Transactions on Knowledge and Data Engineering, 2010, 22(10): 1345-1359.',
    'Deng J, Dong W, Socher R, et al. ImageNet: A Large-Scale Hierarchical Image Database[C]. CVPR, 2009: 248-255.',
    'Paszke A, Gross S, Massa F, et al. PyTorch: An Imperative Style, High-Performance Deep Learning Library[C]. NeurIPS, 2019: 8026-8037.',
]
for i, ref in enumerate(refs, 1):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(f'[{i}] {ref}')
    r.font.size = Pt(10.5)
    r.font.name = 'Times New Roman'

page_break()

# ================= 附录 =================
h1('附录A 提交材料与运行说明')
para('本课程设计随报告提交的完整材料清单如表 A-1 所示。', indent=True)
table(['材料', '内容', '位置/文件'],
      [['完整报告', '本报告（纸质+电子，Word/PDF）', 'docs/智能系统设计与实践报告.docx / .pdf'],
       ['数据集', '花卉102微调数据集（6:2:2 划分）', 'data/flower102/（train/val/test）'],
       ['可运行系统', 'Flask 前端+后端全部源码与依赖清单', 'app/、scripts/、requirements.txt'],
       ['训练模型', '四种模型的微调权重', 'models/*_best.pt'],
       ['分析图表', '训练曲线、混淆矩阵、类别准确率等', 'figures/'],
       ['运行视频', '系统完整演示视频（约2分钟）', 'runs/demo.mp4'],
       ['运行说明', '环境要求与启动步骤', 'docs/运行说明.md'],
       ['分组表', '组员与题目登记表', 'docs/分组表-新建 XLSX 工作表.xlsx']],
      widths=[2.6, 7.2, 6.6], fontsize=9.5)
para('系统运行方式：安装 Python 3.11 与 requirements.txt 中依赖后，在项目根目录执行'
     '“python app/app.py”，浏览器访问 http://127.0.0.1:8000/ 使用识别台，访问 '
     'http://127.0.0.1:8000/admin 使用管理后台。演示视频记录了上传图像、选择三种模型'
     '识别、查看历史记录与进入管理后台的全过程。', indent=True)

doc.save(OUT)
print("report saved:", OUT)
