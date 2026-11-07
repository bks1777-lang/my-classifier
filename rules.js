/* 규칙 분류기 — AI 없이 낱말만으로 가른다. AI와 견줄 기준선이다.
 *   칸: criteria.json 의 priority 순서대로, keywords.json 의 낱말이 처음 걸리는 칸. 없으면 «기타».
 *   긴급도: 높음 낱말이 먼저. 없고 낮음 낱말이 있으면 낮음. 둘 다 없으면 보통.
 */
(function (root) {
  "use strict";

  function hit(text, words) {
    for (const w of words || []) if (text.includes(w)) return w;
    return null;
  }

  function classify(text, criteria, keywords) {
    let category = "기타", whyCat = "어느 칸의 낱말도 없어서 «기타»";
    for (const name of criteria.priority) {
      const w = hit(text, keywords.categories[name]);
      if (w) { category = name; whyCat = `«${w}» 가 있어서 «${name}»`; break; }
    }
    let urgency = "보통", whyUrg = "높음 · 낮음 낱말이 없어서 «보통»";
    const hi = hit(text, keywords.urgency["높음"]);
    const lo = hi ? null : hit(text, keywords.urgency["낮음"]);
    if (hi) { urgency = "높음"; whyUrg = `«${hi}» 가 있어서 «높음»`; }
    else if (lo) { urgency = "낮음"; whyUrg = `«${lo}» 가 있어서 «낮음»`; }
    return { category, urgency, reason: `${whyCat} · ${whyUrg}` };
  }

  // 정답 rows 와 판정 함수로 점수를 낸다. worst = 놓치면 안 되는 칸 이름
  function score(rows, judge, worst) {
    let cat = 0, urg = 0, both = 0, worstTotal = 0, worstMissed = 0;
    const wrong = [];
    rows.forEach((r, i) => {
      const got = judge(r, i);
      const okC = got.category === r.category, okU = got.urgency === r.urgency;
      cat += okC; urg += okU; both += okC && okU;
      if (r.category === worst) { worstTotal++; if (!okC) worstMissed++; }
      if (!okC || !okU) wrong.push({ r, got });
    });
    return { n: rows.length, cat, urg, both, worstTotal, worstMissed, wrong };
  }

  root.Rules = { classify, score };
})(this);
