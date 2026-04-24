import sys
import os
import re
import math
from collections import Counter

try:
    from pdfminer.high_level import extract_text
except ImportError:
    print("Error: pdfminer.six not installed. Run: pip install pdfminer.six")
    sys.exit(1)

try:
    from nltk.stem import PorterStemmer
    stemmer = PorterStemmer()
except ImportError:
    print("Error: nltk not installed. Run: pip install nltk")
    sys.exit(1)

RESUME_BASE = "/Users/abhisheknagaraja/Documents/Job_Automation/core_agents/resume_agent/Resume_Building/Abhishek"
JD_DIR      = os.path.join(os.path.dirname(__file__), "../../data/jds")
MASTER_PDF  = os.path.join(RESUME_BASE, "Master/Abhishek_Nagaraja_Master_Resume.pdf")

# Each entry: (display label, resume PDF path, matching JD file)
ROLES = [
    ("TPM", "Product/Abhishek_Nagaraja_TPM_Resume.pdf",           "jd_tpm.txt"),
    ("PO",  "Product_Owner/Abhishek_Nagaraja_PO_Resume.pdf",      "jd_po.txt"),
    ("BA",  "Business_Analyst/Abhishek_Nagaraja_BA_Resume.pdf",   "jd_ba.txt"),
    ("SM",  "Scrum_Master/Abhishek_Nagaraja_SM_Resume.pdf",       "jd_sm.txt"),
    ("MGR", "Manager/Abhishek_Nagaraja_Manager_Resume.pdf",       "jd_manager.txt"),
    ("GTM", "GTM/Abhishek_Nagaraja_GTM_Resume.pdf",               "jd_gtm.txt"),
]

STOP_WORDS = {
    'the','and','to','of','a','in','is','that','for','it','as','was','with',
    'on','are','be','this','an','at','by','from','or','which','but','not',
    'what','all','were','we','when','your','can','said','there','use','if',
    'will','up','other','about','out','then','them','these','so','some',
    'would','make','like','into','time','has','two','more','than','first',
    'been','call','who','its','now','our','you','have','do','they',
}

# Words that appear in JDs but never belong in resumes
JUNK = {
    'bachelors', 'masters', 'degree', 'years', 'experience', 'related',
    'field', 'looking', 'role', 'highly', 'preferred', 'plus', 'valued',
    'equivalent', 'including', 'such', 'across', 'within', 'between',
    'ensure', 'ability', 'strong', 'familiarity', 'background', 'hands',
    'using', 'work', 'team', 'new', 'key', 'also', 'well', 'both',
    'each', 'multiple', 'large', 'help', 'build', 'take', 'run',
    'conduct', 'perform', 'develop', 'manage', 'lead', 'support',
    'collaborate', 'communicate', 'drive', 'define', 'identify',
    'implement', 'deliver', 'create', 'maintain', 'provide', 'track',
    'ensure', 'coordinate', 'analyze', 'design', 'own', 'apply',
    # JD section headers and boilerplate phrases
    'responsibilities', 'requirements', 'title', 'about', 'seeking',
    'proficiency', 'compelling', 'produce', 'growing', 'always',
    'distractions', 'committed', 'entry', 'level', 'detailed',
    'secure', 'running', 'inform', 'associate',
    'closely', 'clear', 'discussions', 'knowledge', 'information',
    'oriented', 'causes', 'making', 'issue', 'status',
    # Generic verbs / adverbs in JD prose (not skill terms)
    'ensuring', 'through', 'toward', 'stand',
    'update', 'protect', 'detail', 'informed', 'responsible',
}

def clean(text):
    # Split compound tokens (LangChain/LangGraph, AWS(S3), RICE/MoSCoW etc.)
    text = re.sub(r'[/\-\(\),\.]', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return re.sub(r'\s+', ' ', text.lower()).strip()

def stem_tokens(text):
    """Return space-joined string of stemmed tokens for cosine similarity."""
    return ' '.join(stemmer.stem(w) for w in text.split())

def keywords(text):
    """Return set of stemmed, filtered keywords from text."""
    return {stemmer.stem(w) for w in text.split()
            if w not in STOP_WORDS and w not in JUNK and len(w) > 3}

def cosine(t1, t2):
    v1, v2 = Counter(t1.split()), Counter(t2.split())
    num   = sum(v1[x] * v2[x] for x in set(v1) & set(v2))
    denom = math.sqrt(sum(v**2 for v in v1.values())) * math.sqrt(sum(v**2 for v in v2.values()))
    return float(num) / denom if denom else 0.0

def score_resume(resume_clean, jd_clean):
    jd_kw     = keywords(jd_clean)
    resume_kw = keywords(resume_clean)
    matched   = jd_kw & resume_kw
    missing_stems = sorted(jd_kw - resume_kw)
    kw_score  = (len(matched) / len(jd_kw) * 100) if jd_kw else 0

    # Build stem→original word mapping from JD for readable output
    stem_to_word = {}
    for w in jd_clean.split():
        if w not in STOP_WORDS and w not in JUNK and len(w) > 3:
            stem_to_word[stemmer.stem(w)] = w

    missing_words = sorted(stem_to_word.get(s, s) for s in missing_stems)

    # Cosine on stemmed tokens for semantic overlap
    cos_score = cosine(stem_tokens(resume_clean), stem_tokens(jd_clean)) * 100
    # 90% keyword match + 10% cosine — mirrors real ATS scoring (keyword-first)
    final     = (kw_score * 0.9) + (cos_score * 0.1)
    return round(final, 1), round(kw_score, 1), round(cos_score, 1), missing_words

def extract(pdf_path):
    try:
        return clean(extract_text(pdf_path))
    except Exception as e:
        print(f"  ⚠️  Could not read {os.path.basename(pdf_path)}: {e}")
        return None

def bar(s, width=18):
    filled = int(s / 100 * width)
    return "█" * filled + "░" * (width - filled)

def grade(s):
    if s >= 80: return "🟢 STRONG"
    if s >= 65: return "🟡 GOOD"
    if s >= 50: return "🟠 MODERATE"
    return "🔴 WEAK"

def delta(tailored, master):
    d = tailored - master
    if d > 0:  return f"+{d:.1f}"
    if d < 0:  return f"{d:.1f}"
    return "  0.0"

# ── Load JDs ─────────────────────────────────────────────────────────────────
jd_cache = {}
for _, _, jd_file in ROLES:
    jd_path = os.path.join(JD_DIR, jd_file)
    if os.path.exists(jd_path):
        with open(jd_path, encoding="utf-8") as f:
            jd_cache[jd_file] = clean(f.read())
    else:
        print(f"⚠️  Missing JD: {jd_file}")

# ── Load master resume ────────────────────────────────────────────────────────
master_clean = extract(MASTER_PDF)

print(f"\n{'='*70}")
print(f"  ATS ROLE COMPARISON — Tailored Resumes vs Master Resume")
print(f"  (Scoring: stemmed keyword match 90% + stemmed cosine 10%)")
print(f"{'='*70}\n")

results = []

for role, rel_path, jd_file in ROLES:
    pdf_path  = os.path.join(RESUME_BASE, rel_path)
    jd_clean  = jd_cache.get(jd_file)

    if not os.path.exists(pdf_path):
        print(f"  ⚠️  PDF not found: {rel_path}")
        continue
    if not jd_clean:
        continue

    tailored_clean = extract(pdf_path)
    if not tailored_clean:
        continue

    t_final, t_kw, t_cos, t_missing = score_resume(tailored_clean, jd_clean)
    if master_clean:
        m_final, _, _, m_missing = score_resume(master_clean, jd_clean)
    else:
        m_final, m_missing = 0.0, []
    results.append((role, t_final, t_kw, t_cos, m_final, t_missing, m_missing))

# ── Summary table ─────────────────────────────────────────────────────────────
print(f"  {'ROLE':<6} {'TAILORED':>9}  {'MASTER':>7}  {'DELTA':>7}  {'BAR (TAILORED)':<20} {'VERDICT'}")
print(f"  {'─'*6} {'─'*9}  {'─'*7}  {'─'*7}  {'─'*20} {'─'*10}")
for role, t, kw, cos, m, _, __ in results:
    d = delta(t, m)
    print(f"  {role:<6} {t:>8}%  {m:>6}%  {d:>7}  {bar(t):<20} {grade(t)}")

# ── Detail per role ───────────────────────────────────────────────────────────
print(f"\n{'='*70}")
print("  DETAILED BREAKDOWN")
print(f"{'='*70}")

for role, t, kw, cos, m, missing, m_missing in results:
    d = t - m
    arrow = f"▲ +{d:.1f}% vs master" if d > 0 else f"▼ {d:.1f}% vs master"
    print(f"\n  ▶ {role}")
    print(f"    Tailored Score : {t}%  {grade(t)}  ({arrow})")
    print(f"    Master Score   : {m}%  {grade(m)}")
    print(f"    Keyword Match  : {kw}%   |   Cosine Similarity: {cos}%")
    top_missing = [w for w in missing if len(w) > 4][:8]
    if top_missing:
        print(f"    Tailored∅      : {', '.join(top_missing)}")
    top_m_missing = [w for w in m_missing if len(w) > 4][:10]
    if top_m_missing:
        print(f"    Master∅        : {', '.join(top_m_missing)}")

# ── Best / worst ──────────────────────────────────────────────────────────────
if results:
    best  = max(results, key=lambda x: x[1])
    worst = min(results, key=lambda x: x[1])
    best_gain  = max(results, key=lambda x: x[1] - x[4])
    master_worst = min(results, key=lambda x: x[4])
    print(f"\n{'='*70}")
    print(f"  ✅ Highest scoring tailored resume : {best[0]}  ({best[1]}%)")
    print(f"  ⚠️  Lowest scoring tailored resume  : {worst[0]}  ({worst[1]}%)")
    print(f"  📈 Biggest gain over master        : {best_gain[0]}  ({delta(best_gain[1], best_gain[4])}%)")
    print(f"  🎯 Master lowest vs JD             : {master_worst[0]}  ({master_worst[4]}%)")
    print(f"{'='*70}\n")
