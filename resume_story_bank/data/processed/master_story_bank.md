# Master Story Bank

This file is the single-file source of truth for reusable resume stories.

## Story: Blueprint Measurement Framework Correction

### Story ID
SB-101

### Context
At Blueprint, the headline student-improvement KPI (best score minus first score) appeared to overstate gains because of noise, repeated-test variance, and regression-to-the-mean effects.

### Actions
- Identified statistical weaknesses in the existing KPI and additional confounds in practice-test behavior.
- Proposed and implemented an item response theory approach to estimate latent ability across heterogeneous test forms.
- Delivered reports, presentations, screencasts, and meetings to communicate why the prior metric was misleading.

### Outcomes
- Replaced a statistically fragile measurement framing with a more defensible ability-estimation approach.
- Improved internal reasoning quality around student-progress interpretation and KPI validity.

### Skills/Keywords
item response theory, psychometrics, regression to the mean, longitudinal measurement, analytics communication, stakeholder persuasion

### Source References
- /home/daavid/Downloads/master_story_bank (1).md (source story: BP_MEASUREMENT_01)

## Story: Blueprint Knowledge Tracing and Question Selection

### Story ID
SB-102

### Context
Blueprint knowledge tracing and recommendation behavior showed model-performance degradation and unstable question-delivery behavior, especially in lower-sample areas.

### Actions
- Worked on a PyTorch knowledge tracing transformer with feature and architecture updates (including embedding/encoding improvements).
- Produced diagnostic analysis connecting sample-count imbalance to degraded performance on later tests.
- Identified an operational mismatch where high-data questions were not being served.
- Proposed a beta-distribution-based question-selection strategy to reduce oscillation between too-easy and too-hard items.
- Coordinated with engineering/DevOps on inference and postprocessing considerations.

### Outcomes
- Improved diagnosis of model underperformance by tying quality issues to data distribution and serving logic.
- Introduced a more principled probabilistic framing for downstream question selection.

### Skills/Keywords
PyTorch, transformers, knowledge tracing, feature engineering, positional encoding, SageMaker, model diagnostics, recommendation policy, beta distribution

### Source References
- /home/daavid/Downloads/master_story_bank (1).md (source story: BP_KT_DEPLOY_01)

## Story: Government R&D Problem Reframing (Quantum and NLP)

### Story ID
SB-103

### Context
In a government consulting R&D setting, stakeholder asks were often vague or trend-driven and needed reframing into technically credible workflows.

### Actions
- Reframed weakly specified quantum requests into a viable propensity-style modeling pipeline under sparsity.
- Proposed Bayesian hierarchical modeling with partial pooling and a quantum-adjacent feature-selection framing for large lagged feature spaces.
- Built NLP workflows using extraction, embeddings, UMAP, and HDBSCAN under weak labels and data scarcity.
- Bootstrapped early pipeline iterations with synthetic/proxy data, then adapted clustering and diagnostics when noisier real data arrived.
- Helped shape analyst-facing exploratory tooling with timelines, drill-downs, and attribution-style explainability.

### Outcomes
- Converted ambiguous stakeholder goals into actionable, staged proofs of concept.
- Delivered modular exploratory pipelines that balanced MVP speed with later formalization.
- Improved analyst usability through interpretable exploratory views.

### Skills/Keywords
Bayesian hierarchical modeling, partial pooling, embeddings, UMAP, HDBSCAN, NLP clustering, feature selection, exploratory analytics, stakeholder reframing

### Source References
- /home/daavid/Downloads/master_story_bank (1).md (source story: GOV_QUANTUM_NLP_01)

## Story: Dendra Human-in-the-Loop Computer Vision Workflow

### Story ID
SB-104

### Context
At Dendra, ecological drone imagery required expert-validated labeling workflows where ML systems should accelerate domain experts rather than replace them.

### Actions
- Built computer-vision workflows to surface candidate labels for expert confirmation/correction.
- Collaborated with engineering to bridge ingestion and production-adjacent gaps.
- Worked across data, ML engineering, and deployment-adjacent concerns in a greenfield startup environment.

### Outcomes
- Improved annotation throughput and operational usefulness by framing ML as decision support.
- Advanced productization readiness through cross-functional pipeline ownership.

### Skills/Keywords
computer vision, human-in-the-loop ML, aerial imagery, data pipelines, production collaboration, startup ML systems

### Source References
- /home/daavid/Downloads/master_story_bank (1).md (source story: DENDRA_HITL_CV_01)

## Story: Dendra Data Quality and Annotation Reliability

### Story ID
SB-105

### Context
Dendra computer-vision reliability depended heavily on annotation quality, sample selection, and consistency in ambiguous labeling boundaries.

### Actions
- Used active-learning style sample prioritization to target high-leverage labeling effort.
- Investigated label noise via visual-similarity/prediction-mismatch diagnostics.
- Worked directly with annotators and supervised data-labeling activity.
- Helped define annotation best practices for ambiguous edge cases.
- Applied interpretability tools (including LIME and occlusion maps) to support debugging and trust.

### Outcomes
- Improved training-data quality and model reliability through data-centric ML practices.
- Reduced ambiguity in operational labeling via explicit annotation standards.

### Skills/Keywords
active learning, label-noise analysis, annotation QA, data-centric AI, interpretability, LIME, occlusion maps, computer vision operations

### Source References
- /home/daavid/Downloads/master_story_bank (1).md (source story: DENDRA_DATA_QUALITY_01)
