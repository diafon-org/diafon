#!/usr/bin/env python3
"""Sample texts in Diafon for the Reference page (docs/master.md): longer passages read from their ordinary spelling by the
engine (stages.convert: the lexicons for English and Hungarian, the letter stages elsewhere, pinyin for Mandarin)
-> docs/.include/samples.html. The texts are public domain: Aesop's North Wind and the Sun, Article 1 of the
Universal Declaration of Human Rights, Shakespeare, Petőfi."""
import html, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import stages
TEXTS = [
    ('en', 'English', 'The North Wind and the Sun (Aesop)',
     "The North Wind and the Sun were disputing which was the stronger, when a traveler came along wrapped in a warm "
     "cloak. They agreed that the one who first succeeded in making the traveler take his cloak off should be considered "
     "stronger than the other. Then the North Wind blew as hard as he could, but the more he blew the more closely did "
     "the traveler fold his cloak around him; and at last the North Wind gave up the attempt. Then the Sun shined out "
     "warmly, and immediately the traveler took off his cloak. And so the North Wind was obliged to confess that the Sun "
     "was the stronger of the two."),
    ('en', 'English', 'Sonnet 18 (Shakespeare)',
     "Shall I compare thee to a summer's day?\nThou art more lovely and more temperate:\nRough winds do shake the darling "
     "buds of May,\nAnd summer's lease hath all too short a date;\nSometime too hot the eye of heaven shines,\nAnd often is "
     "his gold complexion dimm'd;\nAnd every fair from fair sometime declines,\nBy chance or nature's changing course untrimm'd."),
    ('en', 'English', 'Universal Declaration of Human Rights, Article 1',
     "All human beings are born free and equal in dignity and rights. They are endowed with reason and conscience and "
     "should act towards one another in a spirit of brotherhood."),
    ('hu', 'Hungarian', 'National Song (Sándor Petőfi), first stanza',
     "Talpra magyar, hí a haza!\nItt az idő, most vagy soha!\nRabok legyünk vagy szabadok?\nEz a kérdés, válasszatok!\n"
     "A magyarok istenére\nEsküszünk,\nEsküszünk, hogy rabok tovább\nNem leszünk!"),
    ('hu', 'Hungarian', 'Universal Declaration of Human Rights, Article 1',
     "Minden emberi lény szabadon születik és egyenlő méltósága és joga van. Az emberek, ésszel és lelkiismerettel bírván, "
     "egymással szemben testvéri szellemben kell hogy viseltessenek."),
    ('cs', 'Czech', 'Universal Declaration of Human Rights, Article 1',
     "Všichni lidé rodí se svobodní a sobě rovní co do důstojnosti a práv. Jsou nadáni rozumem a svědomím a mají spolu "
     "jednat v duchu bratrství."),
    ('pl', 'Polish', 'Universal Declaration of Human Rights, Article 1',
     "Wszyscy ludzie rodzą się wolni i równi pod względem swej godności i swych praw. Są oni obdarzeni rozumem i "
     "sumieniem i powinni postępować wobec innych w duchu braterstwa."),
    ('fi', 'Finnish', 'Universal Declaration of Human Rights, Article 1',
     "Kaikki ihmiset syntyvät vapaina ja tasavertaisina arvoltaan ja oikeuksiltaan. Heille on annettu järki ja omatunto, "
     "ja heidän on toimittava toisiaan kohtaan veljeyden hengessä."),
    ('tr', 'Turkish', 'Universal Declaration of Human Rights, Article 1',
     "Bütün insanlar hür, haysiyet ve haklar bakımından eşit doğarlar. Akıl ve vicdana sahiptirler ve birbirlerine karşı "
     "kardeşlik zihniyeti ile hareket etmelidirler."),
    ('sw', 'Swahili', 'Universal Declaration of Human Rights, Article 1',
     "Watu wote wamezaliwa huru, hadhi na haki zao ni sawa. Wote wamejaliwa akili na dhamiri, hivyo yapasa watendeane "
     "kindugu."),
    ('zh', 'Mandarin (pinyin)', 'Universal Declaration of Human Rights, Article 1',
     "ren2ren2 sheng1 er2 zi4you2, zai4 zun1yan2 he2 quan2li4 shang4 yi1lü4 ping2deng3. ta1men fu4you3 li3xing4 he2 "
     "liang2xin1, bing4 ying1 yi3 xiong1di4 guan1xi4 de jing1shen2 xiang1 dui4dai4."),
]
# English translations of the texts in other languages: the Declaration's own English text, and a plain
# line-by-line rendering of Petőfi
UDHR_EN = TEXTS[2][3]
TRANSLATION = {'National Song (Sándor Petőfi), first stanza':
               "Rise, Hungarians, the homeland calls!\nThe time is here, now or never!\nShall we be slaves or free?\n"
               "That is the question, choose!\nBy the God of the Hungarians\nWe swear,\nWe swear that we will be slaves\n"
               "No longer!"}


MARKS = {'1': '\u0304', '2': '\u0301', '3': '\u030c', '4': '\u0300'}


def pinyin_marks(text):
    """Numbered pinyin (zhong1guo2) as it is printed (zhōngguó): the mark on a or e, on the o of ou,
    else on the last vowel; 5 and no digit are the neutral tone."""
    import unicodedata as ud

    def one(m):
        syl, tone = m.group(1).replace('v', 'ü'), m.group(2)
        if tone not in MARKS:
            return syl
        low = syl.lower()
        i = next((low.index(v) for v in 'ae' if v in low), None)
        if i is None:
            i = low.index('o') if 'ou' in low else max(low.rfind(v) for v in 'iouü')
        return ud.normalize('NFC', syl[:i + 1] + MARKS[tone] + syl[i + 1:])
    return re.sub(r"([A-Za-züÜv]+?)([1-5])", one, text)


def para(t): return '<br>'.join(html.escape(l) for l in t.split('\n'))
def main():
    cards, top = [], {}
    for code, lang, title, text in TEXTS:
        if code not in top or 'Human Rights' in title:
            top[code] = title           # the Declaration where there is one: the try-out starts with it
    outs = ['\n'.join(stages.convert(l, 'stage:' + c, 'script') for l in t.split('\n')) for c, _, _, t in TEXTS]
    for (code, lang, title, text), out in zip(TEXTS, outs):
        mark = ' data-top' if top[code] == title else ''
        trans = '' if code == 'en' else (UDHR_EN if 'Human Rights' in title else TRANSLATION.get(title, ''))
        cards.append(f'<article class="sample" data-lang="{code}"{mark}{" hidden" if code != "en" else ""}>'
                     f'<header><span class="sample-lang">{html.escape(lang)}</span>'
                     f'<span class="sample-title">{html.escape(title)}</span></header>'
                     f'<p class="sample-text g">{para(out)}</p><p class="sample-orig">{para(pinyin_marks(text) if code == "zh" else text)}</p>'
                     + (f'<p class="sample-trans">{para(trans)}</p>' if trans else '') + '</article>')
    bar = ('<div class="sample-bar">'
           '<label><input type="range" min="16" max="44" value="24" id="sample-size"> size</label>'
           '<label><input type="checkbox" id="sample-orig" checked> usual spelling</label></div>')
    js = ('<script>(function(){var r=document.querySelector(".samples");if(!r)return;'
          'var s=document.getElementById("sample-size");s.oninput=function(){r.style.setProperty("--sample-size",s.value+"px")};'
          'var o=document.getElementById("sample-orig");o.onchange=function(){r.classList.toggle("no-orig",!o.checked)};})();</script>')
    page = f'<div class="samples" markdown="0">{bar}{"".join(cards)}</div>{js}'
    path = os.path.join(ROOT, 'docs', '.include', 'samples.html'); open(path, 'w').write(page)
    print(f'{path}: {len(TEXTS)} texts')


if __name__ == '__main__':
    main()
