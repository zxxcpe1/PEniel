"""식단표 엑셀(.xlsx) -> mealData.js 변환기

사용법:  python3 tools/convert_meals.py            (저장소의 *식단표*.xlsx 전부 변환)
         python3 tools/convert_meals.py 파일.xlsx ...
연도는 기본 2026, 바꾸려면 MEAL_YEAR=2027 python3 tools/convert_meals.py
"""
import glob, json, os, re, sys, unicodedata
from datetime import date
import openpyxl

YEAR = int(os.environ.get("MEAL_YEAR", "2026"))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUTRI = re.compile(r"^\s*[\d.]+/[\d.]+/[\d.]+/[\d.]+\s*$")
ALLERGY = re.compile(r"\(([\d.]+)\)\s*$")


def split_outside_parens(text):
    parts, depth, cur = [], 0, ""
    for i, ch in enumerate(text):
        depth += ch == "("
        depth -= ch == ")"
        nxt = text[i + 1:i + 2]
        # '간장계란밥*버터/참기름' 처럼 * 뒤 곁들임 사이의 / 는 나누지 않음
        if ch == "/" and depth == 0 and not ("*" in cur and nxt != " "):
            parts.append(cur); cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def parse_item(raw):
    m = ALLERGY.search(raw)
    allergy = [int(x) for x in m.group(1).split(".") if x] if m else []
    name = raw[:m.start()] if m else raw
    return {"name": name.strip().lstrip("*").strip(), "allergy": allergy}


def parse_block(cells):
    """cells: 한 끼(중식/석식)의 셀 문자열 목록 -> dict 또는 None"""
    lines, nutri = [], None
    for c in cells:
        if c is None:
            continue
        s = str(c).strip()
        if not s or "★" in s:
            continue
        if NUTRI.match(s):
            nutri = [float(x) for x in s.split("/")]
            continue
        if s.startswith("(") and lines:      # 윗줄에서 이어지는 알레르기 번호
            lines[-1] += s
        else:
            lines.append(s)
    if not lines:
        return None
    items = [parse_item(p) for line in lines for p in split_outside_parens(line)]
    meal = {"items": items}
    if nutri:
        meal.update(kcal=nutri[0], protein=nutri[1], calcium=nutri[2], iron=nutri[3])
    elif len(items) == 1:                  # '석식없음', '개교기념일' 같은 안내
        meal = {"note": items[0]["name"], "items": []}
    return meal


def convert(path, out):
    ws = openpyxl.load_workbook(path, data_only=True).worksheets[0]
    rows = [list(r)[:6] + [None] * (6 - len(r)) for r in ws.iter_rows(values_only=True)]
    title = unicodedata.normalize("NFC", str(rows[0][0] or os.path.basename(path)))
    month = int(re.search(r"(\d+)\s*월", title).group(1))

    week_rows = [i for i, r in enumerate(rows)
                 if r[0] is None and any(isinstance(v, (int, float)) for v in r[1:6])]
    for wi, start in enumerate(week_rows):
        end = week_rows[wi + 1] if wi + 1 < len(week_rows) else len(rows)
        days = rows[start][1:6]
        labels = [i for i in range(start + 1, end) if rows[i][0] in ("중식", "석식")]
        for li, ls in enumerate(labels):
            le = labels[li + 1] if li + 1 < len(labels) else end
            kind = "lunch" if rows[ls][0] == "중식" else "dinner"
            for col in range(5):
                d = days[col]
                if not isinstance(d, (int, float)):
                    continue
                d = int(d)
                m = month
                nums = [int(x) for x in days if isinstance(x, (int, float))]
                if wi == 0 and any(x < d for x in nums[nums.index(d) + 1:]):
                    m -= 1                              # 첫 주에 섞인 전달 날짜 (예: 30, 31, 1, 2...)
                if wi == len(week_rows) - 1 and any(x > d for x in nums[:nums.index(d)]):
                    m += 1                              # 마지막 주에 섞인 다음달 날짜
                y = YEAR + (m > 12) - (m < 1)
                m = (m - 1) % 12 + 1
                meal = parse_block([rows[i][col + 1] for i in range(ls, le)])
                if meal:
                    key = date(y, m, d).isoformat()
                    out.setdefault(key, {})[kind] = meal
    return title


def main():
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, "**", "*.xlsx"), recursive=True))
    files = [f for f in files if "식단표" in unicodedata.normalize("NFC", os.path.basename(f))]
    data = {}
    for f in files:
        print("변환:", convert(f, data), "<-", os.path.relpath(f, ROOT))
    data = dict(sorted(data.items()))
    js = ("// 자동 생성 파일입니다. 직접 고치지 말고 tools/convert_meals.py 를 다시 실행하세요.\n"
          "// 영양량: kcal(열량) / protein(단백질 g) / calcium(칼슘 mg) / iron(철분 mg)\n"
          "const mealData = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")
    with open(os.path.join(ROOT, "mealData.js"), "w", encoding="utf-8") as fp:
        fp.write(js)
    print(f"mealData.js 저장 완료: {len(data)}일치")


if __name__ == "__main__":
    main()
