# Python ANOVA Skills

CSV 데이터를 입력받아 분산분석이 실행된 Jupyter 노트북을 만드는 Codex 스킬입니다. Codex는 분석할 모형을 먼저 제시하고 사용자가 확인하면 실행합니다. 결과 노트북에는 분산분석표, 주효과 및 교호작용 그래프, 잔차 진단이 포함됩니다.

## 구성

| 스킬 | 역할 |
|---|---|
| [`python-anova`](skills/python-anova/SKILL.md) | 입력을 점검하고 `statsmodels`로 ANOVA를 실행해 `.ipynb`를 저장합니다. |
| [`anova-table-format`](skills/anova-table-format/SKILL.md) | ANOVA 표의 행·열 순서, 숫자 정렬, 소수점과 지수 표기, 빈칸 처리 규칙을 정의합니다. |
| [`report-plot-style`](skills/report-plot-style/SKILL.md) | Matplotlib 그래프와 PNG 표에 공통 글꼴, 색상, 캡션 및 출력 설정을 제공합니다. |

## 샘플 및 데모

[샘플 CSV](examples/balanced_two_way.csv)와 분석 결과가 담긴 [실행 노트북](examples/balanced_two_way_anova.ipynb)을 함께 제공합니다.

[스킬 사용 데모 영상](https://www.youtube.com/watch?v=41CK9Aaxyt0)

## Codex에서 사용

`skills/` 아래의 세 스킬 폴더를 Codex 사용자 스킬 디렉터리에 같은 깊이로 복사합니다. Codex에서 CSV를 첨부하고 `$python-anova`를 호출합니다.

현재 일원·이원 분산분석 및 블록설계를 지원합니다. 사후분석으로 Holm 보정 또는 Fisher LSD를 추가할 수 있습니다.
