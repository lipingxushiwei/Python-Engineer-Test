
import re
from typing import Any, Dict, List, Union, Optional



RegexSpec = Union[str, List[str]]


_CODE_RE = re.compile(r"\b\d{6}\.(?:SH|SZ)\b")

# 日期：
_CN_DATE_RE = re.compile(
    r"(?P<y>\d{4})\s*年\s*(?P<m>\d{1,2})\s*月\s*(?P<d>\d{1,2})(?:\s*[日号])?",
    re.S
)

def normalize_cn_date(m: re.Match) -> str:
    y = int(m.group("y"))
    mo = int(m.group("m"))
    d = int(m.group("d"))
    return f"{y}-{mo:02d}-{d:02d}"


_DATE_RE = re.compile(r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)")

def _extract_section(text: str, key: str) -> str:

    pat = re.compile(
        rf"{re.escape(key)}\s*[：:]\s*(?P<body>.*?)(?=(?:\n\s*[\u4e00-\u9fa5A-Za-z0-9]{2,30}\s*[：:])|\Z)",
        re.S
    )
    m = pat.search(text)
    return m.group("body").strip() if m else ""

def _apply_patterns(text: str, patterns: List[str]) -> Optional[Any]:
    for p in patterns:
        m = re.search(p, text, flags=re.S)
        if not m:
            continue
        if m.groupdict():
            return next(iter(m.groupdict().values()))
        if m.groups():
            return m.group(1)
        return m.group(0)
    return None

def _custom_extract(text: str, field: str) -> Any:
    body = _extract_section(text, field)


    if not body:
        if field == "换股期限":
            body = text
        else:
            return [] if field == "换股期限" else None

    if field == "标的证券":
        m = _CODE_RE.search(body)
        return m.group(0) if m else None

    if field == "换股期限":
        norm = _CN_DATE_RE.sub(normalize_cn_date, body)
        dates = _DATE_RE.findall(norm)
        if len(dates) >= 2:
            return [dates[0], dates[1]]
        return dates

    return body.strip()

def reg_search(text: str, regex_list: List[Dict[str, Union[RegexSpec, str]]]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    for rule in regex_list:
        one: Dict[str, Any] = {}
        for field, spec in rule.items():
            if spec == "*自定义*":
                one[field] = _custom_extract(text, field)
                continue

            patterns = spec if isinstance(spec, list) else [spec]
            body = _extract_section(text, field)

            val = _apply_patterns(body, patterns) if body else None
            if val is None:
                val = _apply_patterns(text, patterns)

            one[field] = val

        results.append(one)

    return results


if __name__ == "__main__":
    text = """
标的证券：本期发行的证券为可交换为发行人所持中国长江电力股份
有限公司股票（股票代码：600900.SH，股票简称：长江电力）的可交换公司债
券。
换股期限：本期可交换公司债券换股期限自可交换公司债券发行结束
之日满 12 个月后的第一个交易日起至可交换债券到期日止，即 2023 年 6 月 2
日至 2027 年 6 月 1 日止。
"""
    regex_list = [{
        "标的证券": "*自定义*",
        "换股期限": "*自定义*"
    }]
    print(reg_search(text, regex_list))

    # [{'标的证券': '600900.SH', '换股期限': ['2023-06-02', '2027-06-01']}]
