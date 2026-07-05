from __future__ import annotations

from typing import Optional
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Printer, PrinterStatusLog

# ---------------------------------------------------------------------------
# HP Error Code Database (20+ entries)
# ---------------------------------------------------------------------------
ERROR_CODE_DB: dict[str, dict] = {
    # Fuser errors (50.x)
    r"50\.[1-4]": {
        "fault_type": "FUSER_LOW_TEMP",
        "root_cause": "定影单元温度过低，定影加热器可能故障或供电异常",
        "severity": "critical",
        "steps": [
            "关闭打印机电源，等待至少 10 分钟",
            "检查定影单元连接线缆是否松动",
            "测量定影加热器电阻值（正常约 10-30 欧姆）",
            "如电阻值异常，更换定影组件",
            "更换电源板（低压电源板可能输出电压不足）",
        ],
        "parts": ["定影组件", "电源板", "定影连接线"],
        "safety": ["更换定影组件前务必断电并等待冷却", "定影单元表面温度可达 200°C"],
        "confidence": 0.85,
    },
    r"50\.[5-9]": {
        "fault_type": "FUSER_HIGH_TEMP",
        "root_cause": "定影单元温度过高，热敏电阻或温控电路故障",
        "severity": "critical",
        "steps": [
            "立即断电，检查定影单元是否有烟雾或烧焦气味",
            "检查热敏电阻是否与定影辊接触良好",
            "测量热敏电阻在室温下的阻值（约 100-300k 欧姆）",
            "如热敏电阻失效，更换定影组件",
            "检查电源板上的温控电路",
        ],
        "parts": ["定影组件", "热敏电阻", "电源板"],
        "safety": ["定影单元高温烫伤风险，断电后至少等待 20 分钟", "如闻到焦味请勿通电，立即联系专业维修"],
        "confidence": 0.85,
    },

    # Paper jam (13.xx)
    r"13\.[01][0-9]": {
        "fault_type": "PAPER_JAM",
        "root_cause": "打印机卡纸，纸张卡在进纸通道某处",
        "severity": "warning",
        "steps": [
            "打开打印机所有舱门",
            "从进纸盘方向轻轻拉出卡纸（顺着走纸方向）",
            "检查定影区域是否有残留纸屑",
            "检查出纸通道是否有卡纸",
            "重新装入纸张并打印测试页",
        ],
        "parts": ["取纸轮", "分离垫", "定影单元（如有纸屑残留）"],
        "safety": ["定影区域高温，避免触碰金属部件", "取出卡纸时注意不要撕裂"],
        "confidence": 0.9,
    },
    r"13\.(1[2-9]|2[0-2])": {
        "fault_type": "PAPER_JAM_DUPLEX",
        "root_cause": "双面打印单元卡纸",
        "severity": "warning",
        "steps": [
            "打开后盖或双面打印单元盖板",
            "取出双面走纸通道中的卡纸",
            "检查双面单元翻转机构是否正常",
            "清洁双面走纸辊",
        ],
        "parts": ["双面打印单元", "翻转导纸板"],
        "safety": [],
        "confidence": 0.85,
    },

    # Supply memory errors (10.xx)
    r"10\.(0[01]|10)": {
        "fault_type": "SUPPLY_MEMORY_ERROR",
        "root_cause": "硒鼓芯片读取失败，芯片接触不良或不兼容",
        "severity": "warning",
        "steps": [
            "取出硒鼓，使用干燥无绒布清洁芯片触点",
            "清洁打印机内部对应触点",
            "重新安装硒鼓并确保卡入到位",
            "若仍报错，更换原装硒鼓",
            "非原装硒鼓可能导致芯片通信问题",
        ],
        "parts": ["硒鼓", "硒鼓芯片（通常随硒鼓一体）"],
        "safety": [],
        "confidence": 0.9,
    },

    # Firmware (49.xx)
    r"49\.[0-9a-fA-F]{2}": {
        "fault_type": "FIRMWARE_CRASH",
        "root_cause": "固件崩溃或打印作业导致固件异常",
        "severity": "critical",
        "steps": [
            "关闭打印机电源，拔掉电源线，等待 2 分钟",
            "重新插上电源线并开机",
            "升级打印机固件至最新版本",
            "检查最近的打印任务是否存在不兼容文件（如特定 PDF 字体）",
            "若频繁出现，执行冷复位 (Cold Reset) 或 NVRAM 初始化",
        ],
        "parts": ["格式化板 (Formatter Board)"],
        "safety": ["NVRAM 初始化会清除所有网络设置，操作前请备份配置"],
        "confidence": 0.8,
    },

    # Motor error (59.xx)
    r"59\.[0-9A-F]{2}": {
        "fault_type": "MOTOR_ERROR",
        "root_cause": "主驱动电机异常，可能是电机卡死或驱动电路故障",
        "severity": "critical",
        "steps": [
            "检查打印机内部是否有异物卡住齿轮组",
            "手动旋转主驱动齿轮，检查是否顺畅",
            "检查电机连接线缆是否松动",
            "测量电机线圈阻值",
            "更换主驱动电机或马达驱动板",
        ],
        "parts": ["主驱动电机", "电机驱动板", "齿轮组"],
        "safety": ["电机及驱动板上可能有高压残留"],
        "confidence": 0.8,
    },

    # Paper feed (11.xx)
    r"11\.[0-9]{2}": {
        "fault_type": "PAPER_FEED_ERROR",
        "root_cause": "进纸失败，纸张未能正常进入走纸通道",
        "severity": "warning",
        "steps": [
            "检查进纸盘中纸张是否放置正确且不过多",
            "检查取纸轮和分离垫是否磨损",
            "清洁取纸轮（使用微湿软布擦拭）",
            "检查纸张是否受潮或粘连",
            "如取纸轮磨损严重，更换取纸轮组件",
        ],
        "parts": ["取纸轮", "分离垫", "进纸离合器"],
        "safety": [],
        "confidence": 0.85,
    },

    # Scanner error (30.xx)
    r"30\.[0-9]{2}": {
        "fault_type": "SCANNER_ERROR",
        "root_cause": "扫描组件故障，扫描头移动异常或传感器错误",
        "severity": "warning",
        "steps": [
            "检查扫描玻璃上有无异物阻挡扫描头移动",
            "清洁扫描导轨并重新润滑",
            "检查扫描头排线是否松动",
            "执行扫描仪校准",
            "更换扫描头组件",
        ],
        "parts": ["扫描头 (CIS/CCD)", "扫描排线", "扫描马达"],
        "safety": ["扫描玻璃锋利边缘，操作时当心划伤"],
        "confidence": 0.8,
    },

    # Door open (20.xx)
    r"20\.[0-9]{2}": {
        "fault_type": "DOOR_OPEN",
        "root_cause": "打印机舱门未正确关闭或门开关传感器故障",
        "severity": "info",
        "steps": [
            "检查所有舱门是否完全关闭",
            "确认硒鼓舱门已扣紧",
            "如所有舱门均已关闭仍报错，检查门开关微动传感器",
            "更换损坏的门开关传感器",
        ],
        "parts": ["门开关微动传感器"],
        "safety": [],
        "confidence": 0.95,
    },

    # Laser scanner error (51.xx)
    r"51\.[0-9]{2}": {
        "fault_type": "LASER_SCANNER_ERROR",
        "root_cause": "激光扫描单元 (LSU) 异常，棱镜马达不转或光束检测失败",
        "severity": "critical",
        "steps": [
            "检查 LSU 快门是否在硒鼓安装时正常打开",
            "检查 LSU 连接线缆",
            "清洁 LSU 反射镜面（使用专用清洁工具）",
            "更换激光扫描单元 (LSU)",
        ],
        "parts": ["激光扫描单元 (LSU)", "LSU 连接线"],
        "safety": ["激光组件请勿直视", "LSU 为精密光学组件，避免震动"],
        "confidence": 0.8,
    },

    # Beam detect error (52.xx)
    r"52\.[0-9]{2}": {
        "fault_type": "BEAM_DETECT_ERROR",
        "root_cause": "激光束检测失败，BD 传感器未检测到激光束",
        "severity": "critical",
        "steps": [
            "检查 LSU 连接线缆",
            "清洁 LSU 内部 BD 传感器窗口",
            "更换激光扫描单元 (LSU)",
            "更换格式化板",
        ],
        "parts": ["激光扫描单元 (LSU)", "格式化板"],
        "safety": [],
        "confidence": 0.8,
    },

    # Transfer roller error (54.xx)
    r"54\.[0-9]{2}": {
        "fault_type": "TRANSFER_ERROR",
        "root_cause": "转印辊异常，转印高压电路故障",
        "severity": "warning",
        "steps": [
            "检查转印辊是否安装正确",
            "清洁转印辊表面",
            "检查高压触点是否良好",
            "更换转印辊",
            "更换高压电源板",
        ],
        "parts": ["转印辊", "高压电源板"],
        "safety": ["高压电源板有高压电，断电后仍有残留"],
        "confidence": 0.8,
    },

    # DC controller error (55.xx)
    r"55\.[0-9]{2}": {
        "fault_type": "DC_CONTROLLER_ERROR",
        "root_cause": "DC 控制板通信异常或硬件故障",
        "severity": "critical",
        "steps": [
            "关闭打印机，重新连接 DC 控制板的所有线缆",
            "检查 DC 控制板上的保险丝",
            "测量各输出电压是否正常",
            "更换 DC 控制板",
        ],
        "parts": ["DC 控制板", "电源板"],
        "safety": ["DC 控制板连接多个高压组件，请断电操作"],
        "confidence": 0.75,
    },

    # Fan error (57.xx)
    r"57\.[0-9]{2}": {
        "fault_type": "FAN_ERROR",
        "root_cause": "散热风扇故障或转速异常",
        "severity": "warning",
        "steps": [
            "检查散热风扇是否有灰尘堵塞",
            "检查风扇连接线",
            "用手转动风扇叶片，检查是否顺畅",
            "更换散热风扇",
        ],
        "parts": ["散热风扇"],
        "safety": [],
        "confidence": 0.9,
    },

    # NVRAM error (68.xx)
    r"68\.[0-9]{2}": {
        "fault_type": "NVRAM_ERROR",
        "root_cause": "NVRAM 数据校验失败或存储芯片故障",
        "severity": "critical",
        "steps": [
            "执行 NVRAM 初始化 (NVRAM Init)",
            "升级固件至最新版本",
            "检查格式化板上的 NVRAM 芯片",
            "更换格式化板",
        ],
        "parts": ["格式化板"],
        "safety": ["NVRAM 初始化会清除所有设置，包括网络配置和计数数据"],
        "confidence": 0.8,
    },

    # Toner cartridge region mismatch (10.100x)
    r"10\.100[0-9]": {
        "fault_type": "REGION_MISMATCH",
        "root_cause": "硒鼓区域码与打印机不匹配",
        "severity": "warning",
        "steps": [
            "确认硒鼓包装上的区域码与打印机一致",
            "更换为对应区域的硒鼓",
            "非正规渠道硒鼓可能区域码不匹配",
        ],
        "parts": ["硒鼓（对应区域）"],
        "safety": [],
        "confidence": 0.95,
    },

    # Engine communication error (79.xx)
    r"79\.[0-9]{2}": {
        "fault_type": "ENGINE_COMM_ERROR",
        "root_cause": "格式化板与引擎控制板通信中断",
        "severity": "critical",
        "steps": [
            "关闭打印机，拔掉电源线，等待 5 分钟",
            "重新连接格式化板与引擎之间的排线",
            "升级固件",
            "更换格式化板与引擎之间的连接排线",
            "更换格式化板",
        ],
        "parts": ["格式化板", "引擎控制板", "FFC 排线"],
        "safety": [],
        "confidence": 0.75,
    },

    # Toner low (10.0001)
    r"10\.000[01]": {
        "fault_type": "TONER_LOW",
        "root_cause": "碳粉余量低，即将耗尽",
        "severity": "info",
        "steps": [
            "准备新硒鼓",
            "当前硒鼓仍可继续使用约 50-100 页",
            "出现打印变淡时更换硒鼓",
        ],
        "parts": ["硒鼓"],
        "safety": [],
        "confidence": 0.95,
    },

    # Waste toner full
    r"(WT_FULL|WASTE_FULL|60\.[0-9]{2})": {
        "fault_type": "WASTE_TONER_FULL",
        "root_cause": "废粉仓已满，需更换或清洁",
        "severity": "warning",
        "steps": [
            "更换废粉收集盒",
            "如为内置废粉仓，更换硒鼓（废粉仓通常集成在硒鼓中）",
            "避免自行清空废粉仓，碳粉粉尘有害健康",
        ],
        "parts": ["废粉收集盒", "硒鼓（如集成废粉仓）"],
        "safety": ["碳粉粉尘可吸入，请佩戴口罩操作", "碳粉遇高温可能产生有害气体"],
        "confidence": 0.9,
    },
}


# ---------------------------------------------------------------------------
# Keyword Pattern Database (15+ entries)
# ---------------------------------------------------------------------------
KEYWORD_PATTERNS: dict[str, str] = {
    r"paper jam|卡纸|paper stuck|jam": "PAPER_JAM",
    r"vertical lines?|条纹|lines on page|streaks": "DRUM_ISSUE",
    r"faint|淡|light print|pale": "TONER_LOW",
    r"no power|不开机|dead|no display|no response": "POWER_ISSUE",
    r"noise|噪音|异响|grinding|squeak|clicking|rattling": "MECHANICAL",
    r"connect|连接|offline|disconnect|not found|unreachable": "NETWORK",
    r"smudge|污渍|dirty|spots|dots|marks": "CLEANING",
    r"wrinkled|褶皱|crease|curled paper|wavy": "FUSER_WEAR",
    r"not feeding|不进纸|feed failure|won.t feed|paper not picking": "FEED_ISSUE",
    r"ghost|重影|double image|shadow print": "TRANSFER",
    r"skewed|歪斜|crooked|misaligned": "ALIGNMENT",
    r"toner dust|漏粉|toner spill|powder": "TONER_LEAK",
    r"scan|扫描|cannot scan|scanner not working": "SCANNER_ISSUE",
    r"error code|错误代码|error \d|code \d": "ERROR_CODE",
    r"driver|驱动|cannot print|print queue|spooler": "DRIVER_ISSUE",
    r"blur|模糊|blurry|out of focus": "OPTICS_DIRTY",
    r"too dark|太黑|overexposed|black page": "EXPOSURE_ISSUE",
    r"background|底灰|gray background|shading": "DRUM_WORN",
    r"no toner|没粉|replace toner|toner empty": "TONER_EMPTY",
    r"blank page|白页|nothing printed|white": "TRANSFER_ROLLER",
}


# ---------------------------------------------------------------------------
# Keyword-to-diagnosis mapping (12+ entries)
# ---------------------------------------------------------------------------
KEYWORD_DIAGNOSIS: dict[str, dict] = {
    "PAPER_JAM": {
        "fault_type": "PAPER_JAM",
        "root_cause": "纸张卡在走纸通道中",
        "severity": "warning",
        "steps": [
            "关闭打印机电源",
            "打开所有舱门检查卡纸位置",
            "顺走纸方向轻轻拉出纸张，避免撕裂",
            "检查定影区域及出纸通道",
            "重新装入纸张，打印测试页",
        ],
        "parts": ["取纸轮（如有磨损）", "分离垫"],
        "safety": ["定影单元高温烫伤风险"],
        "confidence": 0.85,
    },
    "DRUM_ISSUE": {
        "fault_type": "DRUM_ISSUE",
        "root_cause": "感光鼓表面有划痕、污染或老化导致打印出现条纹",
        "severity": "warning",
        "steps": [
            "取出硒鼓，检查感光鼓表面是否有可见划痕",
            "检查感光鼓表面是否有碳粉或油脂污染",
            "如感光鼓有划痕，更换硒鼓",
            "轻微污染可用专用清洁纸清洁",
        ],
        "parts": ["硒鼓（集成感光鼓）", "清洁纸"],
        "safety": ["感光鼓对光敏感，避免长时间暴露在光线下"],
        "confidence": 0.85,
    },
    "TONER_LOW": {
        "fault_type": "TONER_LOW",
        "root_cause": "碳粉余量不足导致打印颜色变淡",
        "severity": "info",
        "steps": [
            "取出硒鼓，轻轻摇晃使残余碳粉均匀分布",
            "如打印效果无明显改善，更换新硒鼓",
            "检查是否设置了省墨模式",
        ],
        "parts": ["硒鼓"],
        "safety": ["摇晃时避免碳粉洒出"],
        "confidence": 0.9,
    },
    "POWER_ISSUE": {
        "fault_type": "POWER_ISSUE",
        "root_cause": "电源供应异常，可能是电源线、电源板或主板故障",
        "severity": "critical",
        "steps": [
            "检查电源线是否牢固连接",
            "测试电源插座是否有电（插入其他设备验证）",
            "检查打印机电源接口是否有松动",
            "测量电源板输出电压是否正常",
            "如电源板正常，检查主板供电电路",
        ],
        "parts": ["电源线", "电源板", "主板"],
        "safety": ["电源板有高压，非专业人员请勿带电操作"],
        "confidence": 0.7,
    },
    "MECHANICAL": {
        "fault_type": "MECHANICAL_ISSUE",
        "root_cause": "机械传动部件磨损、缺油或有异物导致异响",
        "severity": "warning",
        "steps": [
            "打开打印机外壳，目视检查齿轮组有无磨损或断裂",
            "检查是否有异物落入传动机构",
            "对齿轮和轴承添加适量润滑脂",
            "如异响持续，定位具体噪声源后更换对应部件",
        ],
        "parts": ["齿轮组", "轴承", "驱动电机"],
        "safety": ["运转时勿将手伸入机器内部"],
        "confidence": 0.7,
    },
    "NETWORK": {
        "fault_type": "NETWORK_ISSUE",
        "root_cause": "网络连接异常导致打印机离线",
        "severity": "warning",
        "steps": [
            "检查打印机网线是否插好（有线连接）",
            "检查路由器/交换机端口指示灯是否正常",
            "打印配置页检查 IP 地址是否正确获取",
            "尝试在电脑上 ping 打印机 IP",
            "重新连接 Wi-Fi 或更换网线",
            "重启打印机和路由器",
        ],
        "parts": ["网线", "网卡/无线网卡"],
        "safety": [],
        "confidence": 0.85,
    },
    "CLEANING": {
        "fault_type": "CLEANING_NEEDED",
        "root_cause": "打印机内部污染导致打印出现污渍",
        "severity": "info",
        "steps": [
            "执行打印机自动清洁程序",
            "清洁转印辊",
            "清洁定影辊",
            "清洁进纸通道中的纸屑和碳粉残留",
            "如仍有污渍，检查感光鼓表面",
        ],
        "parts": ["清洁纸/清洁布", "转印辊"],
        "safety": ["使用专用清洁用品，避免使用酒精等腐蚀性液体"],
        "confidence": 0.8,
    },
    "FUSER_WEAR": {
        "fault_type": "FUSER_WEAR",
        "root_cause": "定影膜磨损或定影辊老化",
        "severity": "warning",
        "steps": [
            "检查定影膜表面是否有划痕、皱褶或破损",
            "检查定影压力辊是否变形",
            "清洁定影组件",
            "如定影膜破损，更换定影组件",
        ],
        "parts": ["定影组件", "定影膜", "压力辊"],
        "safety": ["定影组件高温，断电后等待至少 20 分钟再操作"],
        "confidence": 0.8,
    },
    "FEED_ISSUE": {
        "fault_type": "FEED_ISSUE",
        "root_cause": "进纸机构故障导致无法取纸",
        "severity": "warning",
        "steps": [
            "检查纸盘是否装纸正确且不过满",
            "检查纸张是否受潮",
            "清洁取纸轮和分离垫",
            "检查分离垫是否磨损（磨损后摩擦力不足）",
            "更换取纸轮或分离垫",
        ],
        "parts": ["取纸轮", "分离垫"],
        "safety": [],
        "confidence": 0.85,
    },
    "TRANSFER": {
        "fault_type": "TRANSFER_ISSUE",
        "root_cause": "转印辊故障或高压异常导致重影",
        "severity": "warning",
        "steps": [
            "清洁转印辊表面",
            "检查转印辊高压触点是否良好",
            "检查转印辊是否安装到位",
            "测量高压电源板输出",
            "更换转印辊",
        ],
        "parts": ["转印辊", "高压电源板"],
        "safety": ["高压电危险"],
        "confidence": 0.75,
    },
    "ALIGNMENT": {
        "fault_type": "ALIGNMENT_ISSUE",
        "root_cause": "走纸通道偏差或进纸盘导纸板未对齐导致打印歪斜",
        "severity": "info",
        "steps": [
            "调整进纸盘导纸板与纸张边缘贴紧",
            "检查纸张是否变形或受潮",
            "执行打印机校准程序",
            "检查走纸辊是否磨损导致纸张偏移",
        ],
        "parts": ["走纸辊"],
        "safety": [],
        "confidence": 0.85,
    },
    "TONER_LEAK": {
        "fault_type": "TONER_LEAK",
        "root_cause": "硒鼓密封破损导致碳粉泄漏",
        "severity": "critical",
        "steps": [
            "立即取出硒鼓，放在报纸上",
            "检查硒鼓外观是否有裂缝",
            "使用专用碳粉吸尘器清理打印机内部洒落的碳粉",
            "更换硒鼓",
            "不要使用普通家用吸尘器（碳粉微粒会穿透滤网）",
        ],
        "parts": ["硒鼓", "碳粉专用吸尘器（清理工具）"],
        "safety": [
            "碳粉粉尘有害，请佩戴口罩和手套",
            "碳粉遇明火可能燃烧",
            "如吸入碳粉，立即到通风处并就医",
        ],
        "confidence": 0.9,
    },
    "SCANNER_ISSUE": {
        "fault_type": "SCANNER_ISSUE",
        "root_cause": "扫描组件故障或连接异常",
        "severity": "warning",
        "steps": [
            "清洁扫描玻璃板",
            "检查扫描头是否移动顺畅",
            "清洁并润滑扫描导轨",
            "检查扫描排线连接",
            "重启打印机后再次测试扫描",
        ],
        "parts": ["扫描头 (CIS)", "扫描排线"],
        "safety": ["扫描玻璃边缘锋利"],
        "confidence": 0.8,
    },
    "ERROR_CODE": {
        "fault_type": "UNKNOWN_ERROR_CODE",
        "root_cause": "打印机报告了错误代码，需要进一步分析",
        "severity": "warning",
        "steps": [
            "记录完整的错误代码",
            "查阅打印机服务手册对应错误代码的含义",
            "根据手册建议进行故障排除",
            "如无法解决，联系技术支持",
        ],
        "parts": [],
        "safety": [],
        "confidence": 0.5,
    },
    "DRIVER_ISSUE": {
        "fault_type": "DRIVER_ISSUE",
        "root_cause": "打印驱动异常、缺失或配置不正确，导致打印机无法正常工作",
        "severity": "warning",
        "steps": [
            "第一步：确认操作系统版本（Windows 10/11、macOS 版本等）",
            "第二步：进入「驱动下载」页面，搜索您的打印机品牌和型号",
            "第三步：下载对应操作系统的最新版本驱动程序",
            "第四步：安装驱动前，先在「控制面板 → 设备和打印机」中删除旧打印机",
            "第五步：运行驱动安装程序，按照向导完成安装",
            "第六步：安装完成后打印测试页验证",
            "如仍无法打印：打开「服务」面板 (services.msc)，找到 Print Spooler 服务并重启",
        ],
        "parts": [],
        "safety": [],
        "confidence": 0.85,
    },
    "OPTICS_DIRTY": {
        "fault_type": "OPTICS_DIRTY",
        "root_cause": "激光器反射镜或透镜污染导致打印模糊",
        "severity": "warning",
        "steps": [
            "使用专用镜头清洁纸擦拭 LSU 反射镜",
            "检查 LSU 快门是否正常开启",
            "清洁感光鼓前的透镜组",
        ],
        "parts": [],
        "safety": ["激光组件请勿直视"],
        "confidence": 0.75,
    },
    "EXPOSURE_ISSUE": {
        "fault_type": "EXPOSURE_ISSUE",
        "root_cause": "曝光参数异常导致打印过黑",
        "severity": "info",
        "steps": [
            "检查打印设置中的浓度/亮度选项",
            "检查是否误设为高浓度模式",
            "检查高压电源偏压是否正常",
            "尝试降低打印浓度",
        ],
        "parts": [],
        "safety": [],
        "confidence": 0.7,
    },
    "DRUM_WORN": {
        "fault_type": "DRUM_WORN",
        "root_cause": "感光鼓老化导致底灰",
        "severity": "warning",
        "steps": [
            "检查感光鼓是否已超过使用寿命",
            "更换硒鼓（感光鼓通常随硒鼓一体）",
            "检查充电辊是否污染",
        ],
        "parts": ["硒鼓"],
        "safety": ["感光鼓对光敏感"],
        "confidence": 0.85,
    },
    "TONER_EMPTY": {
        "fault_type": "TONER_EMPTY",
        "root_cause": "碳粉完全耗尽",
        "severity": "critical",
        "steps": [
            "立即更换硒鼓",
            "确认新硒鼓型号正确",
            "安装后打印测试页确认",
        ],
        "parts": ["硒鼓"],
        "safety": [],
        "confidence": 0.95,
    },
    "TRANSFER_ROLLER": {
        "fault_type": "TRANSFER_ROLLER_FAULT",
        "root_cause": "转印辊故障导致图像无法转印到纸张，输出白页",
        "severity": "warning",
        "steps": [
            "检查转印辊是否安装正确",
            "清洁转印辊高压触点",
            "测量高压是否存在",
            "更换转印辊",
            "更换高压电源板",
        ],
        "parts": ["转印辊", "高压电源板"],
        "safety": ["高压电危险"],
        "confidence": 0.8,
    },
}


async def diagnose(
    db: AsyncSession,
    message: str,
    printer_id: uuid.Optional[UUID] = None,
    session_context: Optional[dict] = None,
) -> dict:
    # Collect printer context and driver info if available
    printer_context = None
    driver_recommendations = None
    if printer_id:
        result = await db.execute(
            select(Printer).where(Printer.id == printer_id)
        )
        printer = result.scalars().first()
        if printer:
            log_result = await db.execute(
                select(PrinterStatusLog)
                .where(PrinterStatusLog.printer_id == printer_id)
                .order_by(PrinterStatusLog.recorded_at.desc())
                .limit(1)
            )
            latest_log = log_result.scalars().first()

            printer_context = {
                "brand": printer.brand,
                "model": printer.model,
                "status": printer.status,
                "toner_level": printer.toner_level,
                "paper_level": printer.paper_level,
                "latest_error_code": latest_log.error_code if latest_log else None,
                "latest_error_message": latest_log.error_message if latest_log else None,
            }

            # Fetch matching drivers for this printer
            from app.models.driver_package import DriverPackage
            drv_result = await db.execute(
                select(DriverPackage)
                .where(
                    DriverPackage.brand == printer.brand,
                    DriverPackage.model == printer.model,
                    DriverPackage.is_active == True,
                )
                .order_by(DriverPackage.version.desc())
                .limit(5)
            )
            drivers = list(drv_result.scalars().all())
            if drivers:
                driver_recommendations = [
                    {"os": d.os_platform, "version": d.version, "id": str(d.id)}
                    for d in drivers
                ]

    # Step 1: Try explicit error code matching
    msg_upper = message.upper()
    for pattern, diagnosis in ERROR_CODE_DB.items():
        if re.search(pattern, msg_upper, re.IGNORECASE):
            result = dict(diagnosis)
            result["matched_pattern"] = pattern
            result["diagnosis_method"] = "error_code_match"
            if printer_context:
                result["printer_context"] = printer_context
            if driver_recommendations:
                result["driver_recommendations"] = driver_recommendations
            return result

    # Step 2: Fall back to keyword matching
    best_match = None
    best_match_len = 0
    for pattern, tag in KEYWORD_PATTERNS.items():
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            match_len = len(match.group(0))
            if match_len > best_match_len:
                best_match_len = match_len
                best_match = tag

    if best_match and best_match in KEYWORD_DIAGNOSIS:
        result = dict(KEYWORD_DIAGNOSIS[best_match])
        result["fault_tag"] = best_match
        result["diagnosis_method"] = "keyword_match"
        if printer_context:
            result["printer_context"] = printer_context
        if driver_recommendations:
            result["driver_recommendations"] = driver_recommendations
        return result

    # Step 3: Check if printer is offline → auto-suggest driver/connection fixes
    if printer_context and printer_context["status"] == "offline":
        steps = [
            f'打印机 {printer_context["brand"]} {printer_context["model"]} 当前处于离线状态',
            "检查 USB 线缆或网络连接是否正常",
            "确认打印机电源已开启",
            "尝试重新安装或更新打印机驱动程序",
        ]
        if driver_recommendations:
            steps.append("以下是适配的驱动程序版本：")
            for drv in driver_recommendations:
                steps.append(f"  - {drv['os']}: v{drv['version']}")
            steps.append("请前往「驱动下载」页面下载对应驱动")
        else:
            steps.append("请前往「驱动下载」页面搜索适配的驱动程序")

        result = {
            "fault_type": "PRINTER_OFFLINE",
            "root_cause": f'{printer_context["brand"]} {printer_context["model"]} 未连接到网络或电源异常',
            "severity": "warning",
            "steps": steps,
            "parts": ["USB 线缆", "网线", "电源线"],
            "safety": [],
            "confidence": 0.85,
            "diagnosis_method": "printer_status_check",
            "printer_context": printer_context,
        }
        if driver_recommendations:
            result["driver_recommendations"] = driver_recommendations
        return result

    # Step 4: No match — return low-confidence response
    steps = [
        "请提供更详细的故障现象描述",
        "如果打印机显示了错误代码，请告知具体代码",
        "描述问题发生前后的操作过程",
        "尝试重启打印机后观察是否仍有问题",
        "检查打印机面板是否有警告指示灯",
    ]
    if printer_context and printer_context["status"] == "online":
        steps.insert(0, f'当前打印机 {printer_context["brand"]} {printer_context["model"]} 状态正常（在线）')
        steps.append(f'碳粉余量：{printer_context["toner_level"]}%  纸张余量：{printer_context["paper_level"]}%')

    result = {
        "fault_type": "UNKNOWN",
        "root_cause": "无法从当前描述中识别明确的故障模式",
        "severity": "info",
        "steps": steps,
        "parts": [],
        "safety": [],
        "confidence": 0.2,
        "diagnosis_method": "fallback",
    }
    if printer_context:
        result["printer_context"] = printer_context
    if driver_recommendations:
        result["driver_recommendations"] = driver_recommendations
    return result


async def predict_failure(
    db: AsyncSession, printer_id: uuid.UUID
) -> dict:
    # Fetch recent status logs
    result = await db.execute(
        select(PrinterStatusLog)
        .where(PrinterStatusLog.printer_id == printer_id)
        .order_by(PrinterStatusLog.recorded_at.desc())
        .limit(100)
    )
    logs = list(result.scalars().all())

    # Fetch printer info
    p_result = await db.execute(
        select(Printer).where(Printer.id == printer_id)
    )
    printer = p_result.scalars().first()

    total_pages = printer.total_pages_printed if printer else 0

    # Count error occurrences
    error_count = sum(1 for log in logs if log.error_code)

    # Analyze toner depletion rate from logs
    toner_readings = [log.toner_level for log in logs if log.toner_level is not None]
    toner_depleting = False
    toner_est_pages = 2000
    if len(toner_readings) >= 3:
        if toner_readings[0] is not None and toner_readings[-1] is not None:
            if toner_readings[-1] > 0:
                toner_depleting = True
                toner_est_pages = int(toner_readings[-1] * 50)  # rough estimate

    component_risks = []

    # Fuser risk (typical fuser life: ~100K-150K pages)
    fuser_life = 120000
    if total_pages > 80000:
        remaining = max(0, fuser_life - total_pages)
        component_risks.append({
            "component": "定影组件 (Fuser)",
            "risk_level": "high" if total_pages > fuser_life * 0.9 else "medium",
            "estimated_remaining_pages": remaining,
            "recommendation": (
                "定影组件已接近使用寿命，建议准备更换备件"
                if total_pages > fuser_life * 0.9
                else "定影组件磨损中，持续监控"
            ),
        })

    # Toner risk
    if toner_readings and toner_readings[0] is not None:
        toner_pct = toner_readings[0]
        toner_risk = "low"
        if toner_pct < 10:
            toner_risk = "high"
        elif toner_pct < 25:
            toner_risk = "medium"

        component_risks.append({
            "component": "碳粉/硒鼓 (Toner Cartridge)",
            "risk_level": toner_risk,
            "estimated_remaining_pages": toner_est_pages,
            "recommendation": (
                "碳粉即将耗尽，立即准备更换硒鼓"
                if toner_pct < 10
                else "碳粉余量偏低，建议提前准备新硒鼓"
                if toner_pct < 25
                else "碳粉余量正常"
            ),
        })

    # Pickup roller risk (typical life: ~50K pages)
    pickup_life = 50000
    if total_pages > 35000:
        remaining = max(0, pickup_life - total_pages)
        component_risks.append({
            "component": "取纸轮 (Pickup Roller)",
            "risk_level": "high" if total_pages > pickup_life * 0.9 else "medium",
            "estimated_remaining_pages": remaining,
            "recommendation": (
                "取纸轮已磨损，建议更换"
                if total_pages > pickup_life * 0.9
                else "取纸轮磨损中，关注进纸情况"
            ),
        })

    # Transfer roller risk
    transfer_life = 80000
    if total_pages > 60000:
        remaining = max(0, transfer_life - total_pages)
        component_risks.append({
            "component": "转印辊 (Transfer Roller)",
            "risk_level": "medium",
            "estimated_remaining_pages": remaining,
            "recommendation": "转印辊接近更换周期，关注打印质量",
        })

    # Laser scanner risk — based on error frequency
    if error_count > 3:
        component_risks.append({
            "component": "激光扫描单元 (LSU)",
            "risk_level": "high" if error_count > 10 else "medium",
            "estimated_remaining_pages": None,
            "recommendation": (
                "LSU 故障频繁，建议更换"
                if error_count > 10
                else "LSU 偶发错误，持续监控"
            ),
        })

    overall_risk = "low"
    if any(r["risk_level"] == "high" for r in component_risks):
        overall_risk = "high"
    elif any(r["risk_level"] == "medium" for r in component_risks):
        overall_risk = "medium"

    return {
        "printer_id": str(printer_id),
        "total_pages_printed": total_pages,
        "recent_error_count": error_count,
        "last_24h_status": printer.status if printer else "unknown",
        "overall_risk": overall_risk,
        "component_risks": component_risks,
    }
