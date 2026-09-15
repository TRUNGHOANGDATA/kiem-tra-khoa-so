# SDD ledger — plan: docs/plan/2026-09-15-tool-kiem-tra-khoa-so-plan.md

Spec: docs/spec/2026-09-15-tool-kiem-tra-khoa-so-design.md (read ✓)
Branch: feat/tool-kiem-tra-khoa-so · MERGE_BASE: 78a5265
Env verified: Python 3.14.4, pandas 3.0.2, openpyxl 3.1.5, xlsxwriter 3.2.9, pywebview 6.2.1, pytest 9.1.1, python-calamine ✓

## Pre-flight conflict scan

### Cross-task rows (tasks sharing a file or interface)

| Tasks | Produces → Consumes | Finding |
|-------|---------------------|---------|
| T0 → T1 | `tests/conftest.py` imports `app.checks.base.BoiCanh` | CONFLICT: T0's own verification step expects pytest to run, but conftest import fails until T1 exists. Plan admits this. |
| T1 → T3..T8 | `tao_ket_qua/bat_dau/co_dong/phat_sinh_theo_prefix/CheckResult` | clean — all consumers use signatures as defined |
| T1 → T12 | `THU_TU_MUC_DO` | T1's Produces list omits `THU_TU_MUC_DO` but its code defines it; T12 imports it. Doc gap only, code consistent. |
| T2 → T11,T12 | `ThongTinFile(path,ten,ky,ky_thang,ky_nam,so_dong,tong_ps,nhat_ky)` | clean — field names match all uses |
| T3..T8 → T9 | 6 × `kiem_tra(df, ctx)` | clean — counts 6+4+3+5+6+5 = 29 matches T9's assertion |
| T9 → T12 | `chay_tat_ca(df, ctx, on_progress)`, `TEN_NHOM` | clean |
| T1,T9 → T10 | `CheckResult` dict keyed by `ma`; uses C4.1, C5.1 | clean — both codes produced by T6/T7 |
| T10 → T11,T12 | `BuocKhoaSo(buoc,trang_thai,tom_tat,ma_check)` | clean |
| T2,T9,T10 → T11 | `xuat_bao_cao(ket_qua,trang_thai,thong_tin,thu_muc_out)` | clean |
| T12 → T14 | `lay_chi_tiet(ma_check,trang,kich_thuoc,tim_kiem)` | clean — app.js passes 4 positional args in same order |
| T13 → T14 | 34 DOM ids | clean — every id app.js touches exists in index.html (verified id-by-id); T13's Produces list omits `khung-chi-tiet`, which index.html does define (doc gap only) |
| T14 → T12 | `onTienTrinh(ten,pct)` global ← `evaluate_js` | clean |

### Per-task self-consistency rows

| Task | Finding |
|------|---------|
| T0 | Self-inconsistent: verification step contradicts the conftest it writes (see T0→T1 above) |
| T1 | clean — 7 tests match the code they exercise |
| T2 | CONFLICT (latent, hits real data): `chuan_hoa` casts account columns with `astype("string")`. If Bravo's `DebitAccount`/`CreditAccount` arrives float64 (any NaN in column), values render `"6421.0"` and every prefix match in T3–T10 silently fails. Tests use object dtype so they pass — the bug only appears on the real 79k file at T15. |
| T3–T8 | clean — traced each assertion against its implementation by hand (C1.2/C1.3, C2.2/C2.3, C3.1/C3.3, C4.1/C4.2/C4.4/C4.5, C5.1/C5.3/C5.4/C5.6, C6.1/C6.5 all compute the asserted values) |
| T9 | clean |
| T10 | clean — 11 steps, order matches spec §5 Tab A; `loc_tong` defined after use but resolved at call time |
| T11 | CONFLICT: `test_ten_sheet_an_toan` expected value is wrong. `"a/b:c*d?[e]"` has 6 illegal chars (`/ : * ? [ ]`) → `"a-b-c-d--e-"`, but the test expects `"a-b-c-d-e-x"...`. Test would fail against correct code. |
| T12 | clean |
| T13 | clean |
| T14 | clean |
| T15 | clean — `so_dong == 79450` matches the measured file |

### Global-constraint rows

| Constraint | Finding |
|------------|---------|
| Commit attribution | CONFLICT: plan hardcodes `Co-Authored-By: Claude Fable 5.1`; current session attribution is `Claude Opus 5`. |
| `.gitignore` contents (T0) | CONFLICT: plan's version omits `.superpowers/` (SDD workspace) and `*.xlsx` (accounting data at repo root). Repo already has the fuller version; T0 would overwrite and start tracking scratch + data. |
| T0 `git init` / branch | CONFLICT: repo already initialised, docs committed, branch `feat/tool-kiem-tra-khoa-so` created during setup. T0 re-running init/branch is redundant. |

## Rulings (pre-flight)

Ruling: Batch T0 + T1 into one dispatch — T0 alone leaves the suite red by construction (its conftest imports T1's module), so the intermediate state is not a reviewable deliverable. Cost if wrong: one review seat covers two small units instead of one; scaffolding defects surface in T1's review rather than their own.

Ruling: T2's `chuan_hoa` must normalise numeric-dtype code columns through `Int64` before `astype("string")`, so `6421.0` → `"6421"` and NaN → `<NA>`; add a regression test feeding a float64 account column. Reason: every prefix-based check in T3–T10 depends on this and the plan's tests cannot catch it. Cost if wrong: a few lines of defensive casting that the real data may never have needed.

Ruling: Replace T11's broken `test_ten_sheet_an_toan` assertions with `ten_sheet_an_toan("a/b:c*d?[e]") == "a-b-c-d--e-"` and `len(ten_sheet_an_toan("x"*40)) == 31`. Reason: implementation is correct (one dash per illegal char); the plan's expected literal miscounted. Cost if wrong: test asserts the actual sanitiser contract instead of the plan's typo.

Ruling: All commits use `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`, overriding the plan's literal. Reason: session attribution guidance supersedes plan text. Cost if wrong: wrong co-author name in history, fixable by rebase.

Ruling: `.gitignore` already exists with `.superpowers/` and `*.xlsx` added; T0 must not overwrite it, and must not re-run `git init` or create a branch. Reason: repo/branch/base commit already established in setup. Cost if wrong: scratch dir or client accounting data enters git history.

Ruling: T1's Produces list omits `THU_TU_MUC_DO` and T13's omits `khung-chi-tiet`; both are defined in the plan's own code blocks. Treated as documentation gaps, not defects — no change. Cost if wrong: nothing; consumers already reference them correctly.

## Progress

Task 0+1: complete (commits 78a5265..414022a, review clean — spec ✅, quality Approved)
Task 0+1: ⚠️ resolved by controller — commit trailers verified `Co-Authored-By: Claude Opus 5` on both commits; `.gitignore` intact incl. `.superpowers/` + `*.xlsx`; `git ls-files` confirms no accounting data tracked.
Task 0+1: minor (deferred): `tao_ket_qua` silently drops a missing COT_CHUAN column instead of raising (app/checks/base.py:106, plan-mandated; each check module's own test asserts full column list, so it self-limits)
Task 0+1: minor (deferred): `so_phat_sinh_tai_khoan` groupby uses default dropna=True, silently excluding null account codes (app/checks/base.py:95-97)
Task 2: complete (commits 414022a..f86448f, review clean — spec ✅, quality Approved). Real-file read 8.42s / 79,450 rows.
Task 2: ⚠️ resolved by controller — trailer `Co-Authored-By: Claude Opus 5` verified on f86448f; branches are only `main` + `feat/tool-kiem-tra-khoa-so`; `git ls-files` shows no data files tracked.
Task 2: minor (deferred): `xac_dinh_ky` all-NaT ValueError branch untested (app/loader.py:75-78)
Task 2: minor (deferred): calamine→openpyxl fallback `except` branch untested (app/loader.py:82-85)
Task 2: minor (deferred): non-integer float in a code column (e.g. `6421.5`) passes through unlogged (app/loader.py:55-58)
Task 2: minor (deferred): brief's Interfaces line claims loader consumes `BoiCanh`/`fmt_so` from base; it does not — stale brief text, no code change needed
Task 2: Ruling: batch the six check modules as 3 dispatches (T3-5 mechanical G1/G2/G3; T6-7 the starred G4 giá vốn + G5 kết chuyển; T8-9 G6 + registry) instead of 6, since each is complete-code transcription of the same shape. Cost if wrong: a defect in one module is reviewed alongside two siblings rather than alone, so a fix round touches a wider diff.

Task 3+4+5: complete (commits f86448f..c0c71ab = 0cd59fd, c420b54, c0c71ab; review clean — spec ✅, quality Approved, no ⚠️). 15 new tests. Trailers verified on all three.
Task 3+4+5: minor (deferred): C1.4 guards only `DebitAccount.notna()`, not CreditAccount — empty-string accounts on both sides would false-positive (app/checks/g1_chung_tu.py:51, plan-mandated)
Task 3+4+5: minor (deferred): new test files cover only each brief's specified scenario — no empty-DataFrame / all-null-account / NaN-Description cases (notably C1.3 `duplicated()` NaN-equality semantics)
Task 3+4+5: minor (deferred): C3.3 built from three groupbys + concat rather than one `groupby().agg()` (app/checks/g3_thue_gtgt.py:135-137, brief's own reference implementation)

Task 6+7: review 1 (Opus) — spec ✅ but quality "Needs fixes": 3 Important + 10 Minor. Trailers verified on d0f8471, 8e85095; app/checks/__init__.py confirmed still 0 bytes.
Task 6+7: Ruling: fix F1 (existence-only closing predicates pass a partial close) by comparing residuals — `ps_no - ps_co` for debit-accumulating accounts, `ps_co - ps_no` for revenue — in C4.4/C5.2/C5.3/C5.4. Reason: Task 10 derives the "Đã làm/Chưa làm" status and Task 12's `san_sang` flag from these, so a false green propagates to the headline verdict, defeating the user's stated priority. Load-bearing for T10/T12. Cost if wrong: partial-close warnings the accountant must dismiss.
Task 6+7: Ruling: C4.5 stays existence-only — a non-zero 154 balance at period end is legitimate sản phẩm dở dang, so a residual test there would fire on every correct manufacturing close. Cost if wrong: a genuinely stalled WIP transfer is reported only by C5.1 at VANG.
Task 6+7: Ruling: fix Minors F4, F5, F8, F9, F11, F12, F13 in the same round — each is a one-liner, and F4/F5/F9 cause recurring false warnings on correct books for this manufacturing client, which erodes trust in the tool faster than a missed check. Cost if wrong: a slightly wider fix diff to review.
Task 6+7: parked — Minor F6 (C5.1 groups by exact account string, so books using `5111` with a `Nợ 511 / Có 911` close yield two rows that net out) — Ruling: fixing it means changing shared `so_phat_sinh_tai_khoan` in base.py that all six modules depend on; defer and validate against the real 79k file at Task 15.
Task 6+7: parked — Minor F7 (negative `Amount` reversal rows trip C4.1's `<= 0`) — Ruling: Bravo's sign convention for bút toán đỏ is unknown and there is no in-repo precedent to judge against; defer to Task 15 real-data validation.
Task 6+7: parked — Minor F10 (C5.4 omits 821 CIT expense) — Ruling: this is a monthly close and CIT is settled quarterly, so a missing `Nợ 911 / Có 8211` is not a monthly defect; C5.1 surfaces any residual at VANG. Cost if wrong: a forgotten CIT close shows as VANG rather than DO.

Task 6+7: fix round 1/5 (13 addressed, 0 open — F1 partial-close residuals, F2 62x ly_do, F3 missing qty/cost columns, F4/F5/F8/F9/F11/F12/F13; commits 8e85095..c58d1da)
Task 6+7: complete (commits c0c71ab..c58d1da = d0f8471, 8e85095, c58d1da; re-review clean, no new breakage, all three "do not change" rulings verified intact). 51 tests passing.
Task 6+7: minor (deferred): `NGUONG_CON_LAI = 0.5` now duplicated in g4 and g5 rather than shared in base.py

Task 8+9: complete (commits c58d1da..85c741c = 7005d2f, 85c741c; review clean — spec ✅, quality Approved). 56 tests. Trailers verified.
Task 8+9: ⚠️ resolved by controller — (a) `so_phat_sinh_tai_khoan` columns `TK/ps_no/ps_co/net` confirmed by Task 1's `test_so_phat_sinh_tai_khoan_co_net`; (b) real file's `DocDate` values are all midnight (`2026-08-01 00:00:00`…`2026-08-31 00:00:00` per the pre-plan data survey), so C6.5's per-day grouping will not fragment — to be re-confirmed at Task 15.
Task 8+9: minor (deferred): inconsistent defensiveness in g6 — C6.1 filters `cols` to present columns while C6.4/C6.5 access `CreatedByName`/`DocDate` unconditionally (app/checks/g6_tong_quan.py:20 vs 81)
Task 8+9: minor (deferred): G6 and registry tests are verbatim transcriptions of their briefs, so "5 new tests passing" confirms transcription accuracy rather than independent verification (reviewer hand-checked the C6.5 arithmetic separately)

Task 10: review 1 (Opus) — spec ✅ vs the brief, but quality "Needs fixes": 4 Important, all plan-mandated, all confirmed by running the module. `trang_thai.py` was written from plan text that predates the Tasks 6-7 corrections, so Tab A now contradicts the checks it cites in `ma_check`.
Task 10: Ruling: fix all four (F1 `_nhom_ve_911` missing residual test green-lights a partial revenue/expense close; F2 step 5 turns C4.1's "could not verify" into an all-clear; F3 VAT step uses prefix 33311 while C5.6 uses 3331; F4 the 154→155 step accepts only 155 while C4.5 accepts 155/157/632). Reason: these are direct fallout from the F1 fix I ordered in Tasks 6-7; leaving them ships a main screen that disagrees with its own detail tab, and Task 12's `san_sang` counts `chua_lam`. Load-bearing for T12/T14. Cost if wrong: a wider diff touching three already-reviewed files.
Task 10: Ruling: also fix F5 (missing check key defaults to a positive assurance), F6 (hoist `TK_KHO` and `NGUONG_CON_LAI` into base.py — their duplication is precisely what caused F3/F4), F7 (five of eleven steps had no assertion; swapping both direction flags would have left the suite green). Cost if wrong: F6 touches g4/g5, so their tests must be re-run to prove behaviour is unchanged.
Task 10: parked — 911↔421 is existence-only, so a wrong-amount profit transfer is caught by no step (C5.1 scopes only accounts 5/6/7/8) — Ruling: inherited from C5.5's design, out of Task 10's scope; carried to the final whole-branch review rather than redesigning C5.5 mid-task.
Task 10: parked — test helper `_suy` runs all 29 checks repeatedly — Ruling: test-time cost only, no correctness impact.

Task 10: fix round 1/5 (7 addressed, 0 open — F1 residual test in `_nhom_ve_911`, F2 C4.1 ghi_chu, F3 VAT prefix 3331, F4 154→155 accepts 155/157/632, F5 missing-key default, F6 constants hoisted to base.py, F7 test assertions; commit 401ed3e..373ae12)
Task 10: complete (commits 85c741c..373ae12 = 401ed3e, 373ae12; re-review clean, all four "do not change" rulings verified intact). 68 tests passing. Re-reviewer confirmed the new tests genuinely fail under both a direction-flag swap and a residual-sign mutation.
Task 10: minor (deferred): `_ket_chuyen` still hardcodes `abs(net) > 0.5` instead of the now-shared `NGUONG_CON_LAI` it sits below (app/trang_thai.py:28) — same value, same duplication class F6 removed elsewhere

Task 11: BLOCKED on first dispatch — implementer correctly refused to patch silently. Plan defect: `_ghi_bang`'s width heuristic `int(df[c].astype(str).str.len().quantile(0.9))` crashes under pandas 3.0, where `astype(str)` leaves `None` as NA, so an all-empty column yields `quantile → NaN` and `int(NaN)` raises. `Description` is exactly such a column in production data, so this would have crashed on real exports, not just the fixture.
Task 11: Ruling: correct the plan — measure width via `df[c].astype("string").fillna("").str.len()` so NA is removed before the quantile (empty frame → 12, all-empty column → floor of 10, populated columns unchanged), and add a regression test with a fully-NA `Description` column, demonstrated failing in RED. Cost if wrong: a slightly wider minimum column in the exported report.

Task 11: complete (commits 373ae12..7ded89b, review clean — spec ✅, quality Approved). 71 tests, suite run under `-W error` with no warnings. Trailer verified; 0 data files tracked.
Task 11: minor (deferred): `assert ws.freeze_panes is not None or True` is a tautology asserting nothing (tests/test_report.py:141, plan-mandated)
Task 11: minor (deferred): no assertion covers the conditional cell colouring or the `Nhat ky xu ly` sheet contents — implemented correctly by inspection, unexercised
Task 11: minor (deferred): numeric-format allowlist omits count columns such as `so_dong` used by C3.3 (app/report.py:86-87, inherited from brief)

Task 12: review 1 — spec ❌ / quality "Needs fixes": 4 Important (2 functional, 2 plan-mandated).
Task 12: Ruling: fix all four — F1 search builds its mask from raw `datetime64` while `_records` displays `dd/mm/yyyy`, so typing the date as shown returns nothing; F2 `kich_thuoc` unclamped defeats the paging design that exists to keep the bridge responsive on the 79k file; F3 `chon_file` is the one public method that can raise, breaking the module's own contract; F4 six of nine methods untested because the test file is the brief's verbatim copy. Cost if wrong: a slightly larger bridge module and more test doubles to maintain.
Task 12: parked — `_records`/`_ghi_bang` date-formatting duplication with report.py — Ruling: deduplicating needs a file outside this task's allowed set; carried to the final whole-branch review.
Task 12: parked — search re-stringifies the frame per call — Ruling: fine at this scale; revisit only if the UI adopts search-as-you-type.
Task 12: parked — `trang <= 0` falls back to page 1 rather than erroring — Ruling: harmless, and an error gives the UI no better option.

Task 12: fix round 1/5 (4 addressed, 0 open — F1 date search, F2 page-size clamp, F3 chon_file guard, F4 test coverage; commit 4e7d315..8fbf156)
Task 12: complete (commits 7ded89b..8fbf156 = 4e7d315, 8fbf156; re-review clean, all rulings intact). 85 tests, clean under `-W error`. Re-reviewer confirmed both regression tests genuinely fail against pre-fix code.
Task 12: minor (deferred): `_records` is now dead code — `lay_chi_tiet` inlines its own `to_json` to avoid double formatting (app/api.py:30-31)

Task 13+14: review 1 — spec ✅ (all 33 DOM ids verified present, all 8 bridge calls correctly shaped, offline/palette/font exact) but quality "Needs fixes": 1 Critical, 1 Important.
Task 13+14: Ruling: fix F1 (Critical) — Excel-sourced strings (customer names, diễn giải) interpolate into `innerHTML` with no escaping anywhere in app.js; a cell containing `<` breaks the row and a crafted value injects markup. Route every backend/Excel-derived string through an `esc()` helper. Cost if wrong: none — escaping is strictly safer.
Task 13+14: Ruling: fix F2 (Important, plan-mandated) — cancelling the file picker returns `None`, which `hienFile` treats as a read failure and shows "Không đọc được file". Distinguish cancel from error. Also fix F3 unstyled banner chips, F4 dead `dataset.ma`, F5 inline style → CSS class, and F6 replace the brief's 11-id sample test with a derived check over all ~33 ids plus an escaping guard. Reason for F6: this UI has no runtime tests, so the static gate is the only thing between a typo and a silent failure in front of the user.
Task 13+14: parked — `muc-do-` class name (trailing hyphen) — Ruling: inherited from the brief; renaming touches the stylesheet and every call site for no functional gain.
Task 13+14: parked — hardcoded numeric-column name list in app.js — Ruling: a mismatch only left-aligns a number; verifying against live column names is Task 15 work.

Task 13+14: fix round 1/5 (6 addressed, 0 open — F1 esc() at every innerHTML sink, F2 cancel-vs-error, F3 chips, F4 dead code, F5 inline style, F6 derived id + escape guard tests; commit 35c8e7e..f960bf6)
Task 13+14: complete (commits 8fbf156..f960bf6 = eaea041, 35c8e7e, f960bf6; re-review clean). 90 tests under `-W error`. Re-reviewer independently confirmed the derived-id regex matches 34 real ids (not a vacuous pass) and all 34 exist in index.html.
Task 13+14: Ruling: the implementer declined to wrap the toast text in `esc()` because `toast()` writes via `textContent`, where escaping would display `&amp;amp;`. That reasoning is correct and I confirm it — my finding text over-listed the sink. Cost if wrong: none; the toast was never an injection sink.
Task 13+14: minor (deferred → folded into Task 15): the fix escapes `b.buoc`/`c.ma`/`c.ten`/`c.ghi_chu` into `tieuDe`, which is consumed only via `textContent`, so a title containing `&`/`<`/`>`/quote would display its entity form. No current check name or ghi_chu contains those characters, so it is latent, but it is a regression this diff introduced — corrected in Task 15 rather than spending another round here.

Task 15: complete (commit f960bf6..28df7df, DONE_WITH_CONCERNS). 91 tests under `-W error`. Real file: `chay_kiem_tra` 9.1–9.7s on 79,450 rows (8.3–8.5s of it the calamine Excel read, <1.5s for all 29 checks). Verdict `san_sang: false`, so_do=4, so_vang=8, so_chua_lam=0. Paging confirmed (C1.1 26,958 rows → 100/page).
Task 15: three deferred items settled on real data, none a bug: C5.1 cross-level grouping does not occur in these books; negative-amount reversals carry `Quantity9 < 0` so C4.1's `> 0` guard already excludes them; the app.js numeric-column list is complete for the columns `lay_chi_tiet` actually returns.
Task 15: the implementer changed no check logic and escalated three noisy checks for a business decision instead — correct call, all three are definitional not numerical: C4.1 (30,502 hits = 38% of file; `UnitCost` is 0 on every issue line while purchase lines carry real prices), C1.4 (2,488 hits; 100% of sampled hits are legitimate DC warehouse / BN bank transfers where the GL account is identical and the distinction lives in a dimension column), C1.1 (26,958 hits; 84.6% carry `ItemName` in place of free-text `Description`).
Task 15: Ruling: do not rule on these three from the desk — C4.1 in particular hinges on a fact only the client holds (whether the 08/2026 weighted-average cost run has been executed). If it has not, C4.1 is exactly the "xác định giá vốn" check the user said is most often forgotten and must stay 🔴; if Bravo simply never exports `UnitCost` on issue lines, the check measures nothing and must change. Asking costs one question; guessing wrong either guts the tool's headline feature or floods it with 30,502 false alarms. Escalated to the user.

FINAL REVIEW (Opus, whole branch 78a5265..28df7df): fit to hand over after four must-fixes, each verified by running it — B1 wrong period silently derived from text dates; B2 `_ket_chuyen`'s `abs(net)` printing a negative remainder and opening an empty evidence table; B3 `mo_file`/`mo_thu_muc` raising, so the post-export toast buttons fail silently; B4 the readiness verdict ignoring all yellow checks and all `can_ra` steps, turning green with 8 yellows outstanding.
FINAL FIX WAVE: commits 28df7df..f462784 (1d7222f A, 46b6065 B, a7a247a C, f462784 D). 91 → 168 tests, clean under `-W error`. Real file after the client's rule changes: C1.1 26,958 → 4,157; C1.4 2,488 → 0; verdict `chua_san_sang`, 3 đỏ / 8 vàng / 3 cần rà.
Ruling (client decisions, from the user directly): C4.1 stays 🔴 and keeps its detail rows but must read as one action in Tab A; C1.4 excludes transfer vouchers DC/LR/BN/BT; C1.1 treats `ItemName` as a valid description.
Ruling: A1's detection rule as I first specified it ("not one stock row is priced") never fires — 2,017 issue rows are priced against 30,502 unpriced. Replaced with a proportion rule (≥80% unpriced, minimum 100 rows) and softened the wording to "phần lớn dòng xuất kho chưa có đơn giá". Reason: the client's intent — warn, as one action — is unchanged; only my certainty was wrong. Cost if wrong: a file where genuinely 20%+ of issues are unpriced reads as "not yet costed" when it is merely incomplete.
Ruling: accepted the implementer's rejection of my prescribed blanket `dayfirst=True` for B1 — on pandas 3.0.2 it turns `yyyy-mm-dd` into NaT, trading one silent wrong-period bug for another, and their existing test caught it. Their `doc_ngay()` (year-first parsed straight, `dayfirst` for the rest) stands.
Ruling: fix the two latent items the implementer logged rather than parking them (unevidenced `chua_lam` when `ps_no == 0 < ps_co`; step 11 reading `da_lam` on an empty frame) — both are the step-vs-evidence disagreement class, now found six times on this branch, and the D1 property test should cover them.
Parked at final review: Tab A / Tab B answer different questions so a `can_ra` step citing a red check is acceptable; `lay_chi_tiet` re-stringifying per search (0.24s behind a 300ms debounce); `muc-do-` class name; `so_phat_sinh_tai_khoan` dropna and `tao_ket_qua`'s column drop (both verified unreachable); 911↔421 wrong-amount blind spot (needs opening balances the file does not carry — documented in C5.5's ghi_chu instead).

A1 follow-up: commit f6b4a9a. 176 tests. Real file: ratio 30,502/32,519 = 0.938 fires; step 5 now `chua_lam` "Chưa tính giá xuất kho bình quân cuối kỳ — 30502/32519 dòng xuất kho chưa có đơn giá". Headline `chua_san_sang` "còn 4 việc" (was 3 — the costing step moved from `can_ra` into `chua_lam`, which is the client's intent).
A1 follow-up: Ruling accepted from the implementer — the ratio denominator is stock **issue** rows (Có TK kho) with quantity, not all stock rows. Over all stock rows the ratio is 0.663 and would not clear 0.8. Receipt lines always carry a purchase price, so including them dilutes the signal, and "dòng xuất kho" is what the wording promises. Cost if wrong: a period with unusually few issues could trip the rule on a small sample — guarded by SO_DONG_XUAT_TOI_THIEU = 100.
SCOPED RE-REVIEW of the fix wave (Opus, 28df7df..f6b4a9a): all 24 items + the follow-up ruling ADDRESSED; two ADDRESSED WITH CAVEAT. Verdict: **Ready with noted caveats**. B4 verified undriftable (one shared `tinh_ket_luan`, both call sites). A1 verified firing at 0.938 and bounded both sides. C4's `TEN_COT` verified to cover exactly the union of all 29 checks' emitted columns — no gap. No violation of the ordered-not-changed list.
RESIDUALS surfaced to the user rather than fixed (the process allows one fix wave and one scoped re-review, both spent): (1) MEDIUM, pre-existing — `_nhom_ve_911` admits an account on `any(...)`, which is true for a purely negative total, while `_thieu` requires `> 0`; a P&L account with only negative movement yields `chua_lam` citing an empty C5.3/C5.4. Seventh instance of the step-vs-evidence class; D1 cannot see it because `KICH_BAN` has no negative-amount scenario, and the real file does carry 243 negative rows. (2) LOW, latent — `g3_thue_gtgt.py:17` builds the voucher key as `DocCode + "" + DocNo` with no separator, so `("AB","1")` and `("A","B1")` would collide; inert today because every DocCode is 2 chars.
GUI verified by the controller: `python -m app.main` launches clean, no traceback, window open.

Task 0+1: Ruling: set repo-local git identity to L. Jennings <l.jennings@advantagevillageacademy.org> so every later commit is consistent — the implementer had none configured and improvised per-commit env vars. Cost if wrong: commits attributed to the user's work email in a purely local repo; changeable with git config + rebase.
