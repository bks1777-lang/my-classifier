/* 가림 — AI에 보내기 전에, 브라우저 안에서.
 * 이름 · 전화번호 · 학교 이름을 [이름] [전화번호] [학교] 로 바꾼다.
 * 자동 가림은 완벽하지 않다. 무엇을 놓치는지 시험해서 안다.
 */
(function (root) {
  "use strict";

  const SURNAMES = "김이박최정강조윤장임한오서신권황안송류홍전고문양손배백허유남심노하곽성차주우구민나진지엄채원천방공현함변염여추도소석선설마길연위표명기반왕금옥육인맹제모";

  const PATTERNS = [
    { type: "전화번호", re: /0\d{1,2}[- ]?\d{3,4}[- ]?\d{4}/g },
    // ○○초등학교 · ○○중학교 · ○○고등학교 · ○○학교 — 붙여 쓴 이름만 잡는다 («저희 학교» 는 그대로)
    { type: "학교", re: /[가-힣]{2,}(?:초등학교|중학교|고등학교|학교)/g },
    // 성씨 + 두 글자 뒤에 «입니다 · 님 · 선생님 · 주무관 · 영양사 · 영양교사» 가 올 때
    { type: "이름", re: new RegExp(`(?<![가-힣])[${SURNAMES}][가-힣]{2}(?=\\s?(?:입니다|님|선생님|주무관|영양사|영양교사))`, "g") },
  ];

  function mask(text) {
    let out = String(text || "");
    const found = [];
    for (const p of PATTERNS) {
      out = out.replace(p.re, m => { found.push({ type: p.type, value: m }); return `[${p.type}]`; });
    }
    return { masked: out, found };
  }

  root.Mask = { mask };
})(this);
