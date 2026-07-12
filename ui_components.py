

import json

_FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;"
    "9..144,700&family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500&display=swap');"
)

_PALETTE = """
  --lamp-gold: #e8b84b;
  --lamp-gold-lt: #ffe9a8;
  --brass: #c89b3c;
  --parchment: #f3e7cc;
  --parchment-2: #ece0c2;
  --parchment-ink: #2a2118;
  --fountain-teal: #4c8577;
  --sealing-wax: #a5455a;
  --cream-soft: #efe3c8;
"""


def _safe_json(data) -> str:
    """Embed Python data as JS-safe JSON (guards against closing </script> tags)."""
    return json.dumps(data).replace("</", "<\\/")


def build_flashcard_html(flashcards: list) -> str:
    data_json = _safe_json(flashcards)
    return f"""
<div id="fc-root"></div>
<style>
  {_FONT_IMPORT}
  #fc-root {{
    --lamp-gold: #e8b84b; --lamp-gold-lt: #ffe9a8; --brass: #c89b3c;
    --parchment: #f3e7cc; --parchment-2: #ece0c2; --parchment-ink: #2a2118;
    --fountain-teal: #4c8577; --sealing-wax: #a5455a; --cream-soft: #efe3c8;
    font-family: 'Inter', sans-serif;
    display: flex; flex-direction: column; align-items: center;
    color: var(--cream-soft); padding: 14px 10px; box-sizing: border-box;
  }}
  .fc-counter {{
    font-family: 'Space Grotesk', sans-serif; font-size: 12.5px; font-weight: 600;
    letter-spacing: 0.6px; text-transform: uppercase; opacity: 0.75; margin-bottom: 14px;
  }}
  .fc-scene {{ width: 100%; max-width: 520px; height: 250px; perspective: 1400px; }}
  .fc-card {{
    position: relative; width: 100%; height: 100%;
    transition: transform 0.55s cubic-bezier(.4,.2,.2,1);
    transform-style: preserve-3d; cursor: pointer;
  }}
  .fc-card.flipped {{ transform: rotateY(180deg); }}
  .fc-pin {{
    position: absolute; top: -8px; left: 50%; transform: translateX(-50%);
    width: 16px; height: 16px; border-radius: 50%; z-index: 3;
    background: radial-gradient(circle at 35% 30%, #ffe9a8, #c89b3c 70%, #7a5b1f 100%);
    box-shadow: 0 3px 5px rgba(0,0,0,0.45);
  }}
  .fc-face {{
    position: absolute; inset: 0; backface-visibility: hidden;
    border-radius: 6px; display: flex; align-items: center; justify-content: center;
    text-align: center; padding: 30px 26px; font-size: 18px; font-weight: 500;
    line-height: 1.55;
    box-shadow: 0 16px 34px rgba(0,0,0,0.45), inset 0 0 0 1px rgba(255,255,255,0.25);
  }}
  .fc-front {{
    font-family: 'Fraunces', serif; font-weight: 600; font-size: 21px;
    background:
      radial-gradient(circle at 15% 20%, rgba(0,0,0,0.03) 0, transparent 2px),
      radial-gradient(circle at 75% 70%, rgba(0,0,0,0.03) 0, transparent 2px),
      linear-gradient(178deg, var(--parchment), var(--parchment-2));
    background-size: 8px 8px, 9px 9px, 100% 100%;
    color: var(--parchment-ink);
    border-left: 4px solid var(--lamp-gold);
  }}
  .fc-back {{
    font-family: 'Inter', sans-serif;
    background:
      radial-gradient(circle at 20% 25%, rgba(0,0,0,0.03) 0, transparent 2px),
      linear-gradient(178deg, #ece7da, #e3ddc8);
    color: var(--parchment-ink);
    transform: rotateY(180deg);
    border-left: 4px solid var(--fountain-teal);
  }}
  .fc-hint {{ font-family: 'Space Grotesk', sans-serif; font-size: 12px; opacity: 0.65; margin-top: 12px; }}
  .fc-controls {{ display: flex; gap: 12px; margin-top: 18px; flex-wrap: wrap; justify-content: center; }}
  .fc-btn {{
    background: linear-gradient(180deg, rgba(232,184,75,0.18), rgba(232,184,75,0.06));
    border: 1px solid rgba(232,184,75,0.35);
    color: var(--cream-soft); padding: 9px 18px; border-radius: 8px; cursor: pointer;
    font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 13.5px;
    transition: transform .15s ease, background .15s ease, border-color .15s ease;
  }}
  .fc-btn:hover {{ background: rgba(232,184,75,0.22); border-color: var(--lamp-gold); transform: translateY(-2px); }}
  .fc-progress {{ width: 100%; max-width: 520px; height: 5px; background: rgba(239,227,200,0.12); border-radius: 4px; margin-top: 20px; overflow: hidden; }}
  .fc-progress-bar {{ height: 100%; background: linear-gradient(90deg, var(--fountain-teal), var(--lamp-gold)); transition: width .3s ease; }}
</style>
<script>
(function() {{
  const cards = {data_json};
  let idx = 0;
  let flipped = false;
  const root = document.getElementById('fc-root');

  function render() {{
    if (!cards || cards.length === 0) {{
      root.innerHTML = '<p>No flashcards were generated. Try regenerating.</p>';
      return;
    }}
    const card = cards[idx];
    root.innerHTML = `
      <div class="fc-counter">Flashcard ${{idx + 1}} of ${{cards.length}}</div>
      <div class="fc-scene">
        <div class="fc-card ${{flipped ? 'flipped' : ''}}" id="fc-card">
          <div class="fc-pin"></div>
          <div class="fc-face fc-front">${{card.front}}</div>
          <div class="fc-face fc-back">${{card.back}}</div>
        </div>
      </div>
      <div class="fc-hint">Click the card to flip it</div>
      <div class="fc-controls">
        <button class="fc-btn" id="fc-prev">&larr; Prev</button>
        <button class="fc-btn" id="fc-shuffle">Shuffle</button>
        <button class="fc-btn" id="fc-next">Next &rarr;</button>
      </div>
      <div class="fc-progress"><div class="fc-progress-bar" style="width:${{((idx + 1) / cards.length) * 100}}%"></div></div>
    `;
    document.getElementById('fc-card').onclick = () => {{ flipped = !flipped; render(); }};
    document.getElementById('fc-prev').onclick = () => {{ idx = (idx - 1 + cards.length) % cards.length; flipped = false; render(); }};
    document.getElementById('fc-next').onclick = () => {{ idx = (idx + 1) % cards.length; flipped = false; render(); }};
    document.getElementById('fc-shuffle').onclick = () => {{
      for (let i = cards.length - 1; i > 0; i--) {{
        const j = Math.floor(Math.random() * (i + 1));
        [cards[i], cards[j]] = [cards[j], cards[i]];
      }}
      idx = 0; flipped = false; render();
    }};
  }}
  render();
}})();
</script>
"""


def build_quiz_html(questions: list) -> str:
    data_json = _safe_json(questions)
    return f"""
<div id="qz-root"></div>
<style>
  {_FONT_IMPORT}
  #qz-root {{
    --lamp-gold: #e8b84b; --lamp-gold-lt: #ffe9a8; --brass: #c89b3c;
    --fountain-teal: #4c8577; --sealing-wax: #a5455a; --cream-soft: #efe3c8;
    font-family: 'Inter', sans-serif; color: var(--cream-soft);
    max-width: 660px; margin: 0 auto; padding: 12px 8px; box-sizing: border-box;
  }}
  .qz-progress {{ width: 100%; height: 5px; background: rgba(239,227,200,0.12); border-radius: 4px; margin-bottom: 20px; overflow: hidden; }}
  .qz-progress-bar {{ height: 100%; background: linear-gradient(90deg, var(--fountain-teal), var(--lamp-gold)); transition: width .3s ease; }}
  .qz-question {{
    font-family: 'Fraunces', serif; font-weight: 600; font-size: 20px;
    margin-bottom: 18px; line-height: 1.5; color: var(--lamp-gold-lt);
  }}
  .qz-option {{
    display: flex; align-items: center; gap: 12px; width: 100%; text-align: left;
    background: rgba(239,227,200,0.05); border: 1px solid rgba(239,227,200,0.16);
    color: var(--cream-soft); padding: 12px 16px; border-radius: 8px; margin-bottom: 10px;
    cursor: pointer; font-family: 'Inter', sans-serif; font-size: 15px;
    transition: background .15s ease, transform .15s ease, border-color .15s ease;
  }}
  .qz-bubble {{
    flex: 0 0 auto; width: 18px; height: 18px; border-radius: 50%;
    border: 2px solid rgba(239,227,200,0.4); position: relative;
  }}
  .qz-option:hover:not(:disabled) {{ background: rgba(239,227,200,0.1); transform: translateX(4px); border-color: rgba(232,184,75,0.4); }}
  .qz-option.correct {{ background: rgba(76,133,119,0.28) !important; border-color: var(--fountain-teal); }}
  .qz-option.correct .qz-bubble {{ border-color: var(--fountain-teal); background: var(--fountain-teal); }}
  .qz-option.wrong {{ background: rgba(165,69,90,0.28) !important; border-color: var(--sealing-wax); }}
  .qz-option.wrong .qz-bubble {{ border-color: var(--sealing-wax); background: var(--sealing-wax); }}
  .qz-explain {{
    margin-top: 14px; padding: 14px 16px; background: rgba(239,227,200,0.05);
    border-left: 3px solid var(--lamp-gold); border-radius: 6px; font-size: 14px; line-height: 1.55;
  }}
  .qz-next {{
    margin-top: 18px;
    background: linear-gradient(180deg, var(--lamp-gold-lt), var(--lamp-gold) 55%, var(--brass));
    border: 1px solid rgba(255,255,255,0.4); color: #2a1c05; padding: 10px 22px;
    border-radius: 8px; cursor: pointer; font-weight: 700; font-family: 'Space Grotesk', sans-serif;
    font-size: 14px; transition: transform .15s ease;
  }}
  .qz-next:hover {{ transform: translateY(-2px); }}
  .qz-score-ring {{ width: 160px; height: 160px; border-radius: 50%; margin: 22px auto; display: flex; align-items: center; justify-content: center; }}
  .qz-score-inner {{
    background: #241a12; width: 122px; height: 122px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-family: 'Space Grotesk', sans-serif; font-size: 26px; font-weight: 700; color: var(--lamp-gold-lt);
  }}
  .qz-final {{ text-align: center; }}
  .qz-final h3 {{ font-family: 'Fraunces', serif; color: var(--lamp-gold-lt); }}
  .qz-restart {{
    margin-top: 16px; background: rgba(239,227,200,0.07); border: 1px solid rgba(232,184,75,0.35);
    color: var(--cream-soft); padding: 10px 20px; border-radius: 8px; cursor: pointer;
    font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 14px;
  }}
  .qz-restart:hover {{ border-color: var(--lamp-gold); }}
</style>
<script>
(function() {{
  const questions = {data_json};
  let idx = 0, score = 0, answered = false;
  const root = document.getElementById('qz-root');

  function render() {{
    if (!questions || questions.length === 0) {{
      root.innerHTML = '<p>No quiz questions were generated. Try regenerating.</p>';
      return;
    }}
    if (idx >= questions.length) {{
      const pct = Math.round((score / questions.length) * 100);
      root.innerHTML = `
        <div class="qz-final">
          <h3>Quiz Complete</h3>
          <div class="qz-score-ring" style="background:conic-gradient(var(--lamp-gold) ${{pct * 3.6}}deg, rgba(239,227,200,0.12) 0deg);">
            <div class="qz-score-inner">${{pct}}%</div>
          </div>
          <p>You scored ${{score}} out of ${{questions.length}}</p>
          <button class="qz-restart" id="qz-restart">Retake Quiz</button>
        </div>`;
      document.getElementById('qz-restart').onclick = () => {{ idx = 0; score = 0; answered = false; render(); }};
      return;
    }}
    const q = questions[idx];
    const pct = (idx / questions.length) * 100;
    root.innerHTML = `
      <div class="qz-progress"><div class="qz-progress-bar" style="width:${{pct}}%"></div></div>
      <div class="qz-question">Q${{idx + 1}}. ${{q.question}}</div>
      <div id="qz-options"></div>
      <div id="qz-extra"></div>
    `;
    const optWrap = document.getElementById('qz-options');
    (q.options || []).forEach((opt, i) => {{
      const btn = document.createElement('button');
      btn.className = 'qz-option';
      btn.innerHTML = '<span class="qz-bubble"></span><span>' + opt + '</span>';
      btn.onclick = () => selectAnswer(i);
      optWrap.appendChild(btn);
    }});
  }}

  function selectAnswer(i) {{
    if (answered) return;
    answered = true;
    const q = questions[idx];
    const opts = document.querySelectorAll('.qz-option');
    opts.forEach((b, bi) => {{
      if (bi === q.answer_index) b.classList.add('correct');
      else if (bi === i) b.classList.add('wrong');
      b.disabled = true;
    }});
    if (i === q.answer_index) score++;
    const extra = document.getElementById('qz-extra');
    extra.innerHTML = `
      <div class="qz-explain">${{q.explanation || ''}}</div>
      <button class="qz-next" id="qz-next">${{idx + 1 < questions.length ? 'Next Question' : 'See Results'}}</button>
    `;
    document.getElementById('qz-next').onclick = () => {{ idx++; answered = false; render(); }};
  }}

  render();
}})();
</script>
"""
