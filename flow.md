# AI CSV Assistant - Architecture Flowcharts

## Current Architecture

```mermaid
flowchart TD
    A[User Uploads CSV/Excel] --> B[File Processing]
    B --> C[DataFrame Creation]
    C --> D[User Input: Natural Language Query]
    D --> E[Intent Extraction & Slot Filling]
    E --> F{Template Match?}
    F -->|Yes| G[Instant Code Generation]
    F -->|No| H[LLM Code Generation]
    H --> I[Code Safety Check]
    I --> J{Code Safe?}
    J -->|No| K[Error: Unsafe Code Blocked]
    J -->|Yes| L[Execute Code]
    G --> L
    L --> M[Display Results]
    M --> N[Updated DataFrame]
    N --> O[Download Option]
    O --> P[CSV/Excel Export]
    
    style A fill:#e1f5fe
    style D fill:#fff3e0
    style H fill:#f3e5f5
    style L fill:#e8f5e8
    style K fill:#ffebee
```

## Proposed Agentic Framework Architecture

i want you to see the current ode struture and suggest e how i can add more features o it ad transformit into a proper web app with agenbtc framewrok with agents and superviser and ui betteer , recomenneation, chyarting style and all
```mermaid
flowchart TD
    A[User Uploads CSV/Excel] --> B[Data Profiling Agent]
    B --> C[Data Quality Assessment]
    C --> D[Supervisor Agent]
    D --> E[Task Analysis & Delegation]
    
    E --> F[Data Analyst Agent]
    E --> G[Visualization Agent]
    E --> H[Data Engineer Agent]
    E --> I[QA Agent]
    
    F --> J[Statistical Analysis]
    F --> K[Insights Generation]
    F --> L[Trend Detection]
    
    G --> M[Chart Recommendations]
    G --> N[Interactive Visualizations]
    G --> O[Dashboard Creation]
    
    H --> P[Data Cleaning]
    H --> Q[Transformations]
    H --> R[ETL Operations]
    
    I --> S[Result Validation]
    I --> T[Quality Checks]
    I --> U[Error Detection]
    
    J --> V[Result Aggregation]
    K --> V
    L --> V
    M --> V
    N --> V
    O --> V
    P --> V
    Q --> V
    R --> V
    S --> V
    T --> V
    U --> V
    
    V --> W[Supervisor Review]
    W --> X[User Interface]
    X --> Y[Interactive Dashboard]
    X --> Z[Download Options]
    X --> AA[Share & Export]
    
    style A fill:#e1f5fe
    style D fill:#fff3e0
    style F fill:#e8f5e8
    style G fill:#f3e5f5
    style H fill:#fff8e1
    style I fill:#fce4ec
    style W fill:#e0f2f1
```

## Multi-Agent Communication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant S as Supervisor Agent
    participant DA as Data Analyst Agent
    participant VA as Visualization Agent
    participant DE as Data Engineer Agent
    participant QA as QA Agent
    
    U->>S: Upload CSV + Query
    S->>S: Analyze Task & Context
    S->>DA: Request Statistical Analysis
    S->>VA: Request Visualization
    S->>DE: Request Data Cleaning
    
    DA->>S: Return Analysis Results
    VA->>S: Return Chart Recommendations
    DE->>S: Return Cleaned Data
    
    S->>QA: Validate All Results
    QA->>S: Quality Assessment
    
    S->>S: Aggregate & Synthesize
    S->>U: Present Comprehensive Results
    
    Note over S: Memory System<br/>Stores conversation history<br/>and context for future queries
```

## Enhanced UI Architecture

```mermaid
flowchart LR
    subgraph "Main Application"
        A[Landing Page] --> B[File Upload]
        B --> C[Data Overview]
        C --> D[Analysis Dashboard]
        C --> E[Visualization Studio]
        C --> F[Data Engineering]
        C --> G[Collaboration Hub]
    end
    
    subgraph "Analysis Dashboard"
        D --> D1[Quick Insights]
        D --> D2[Statistical Analysis]
        D --> D3[ML Recommendations]
        D --> D4[Business Intelligence]
    end
    
    subgraph "Visualization Studio"
        E --> E1[Chart Gallery]
        E --> E2[Interactive Plots]
        E --> E3[Custom Dashboards]
        E --> E4[Export Options]
    end
    
    subgraph "Data Engineering"
        F --> F1[Data Cleaning]
        F --> F2[Transformations]
        F --> F3[ETL Pipelines]
        F --> F4[Quality Monitoring]
    end
    
    subgraph "Collaboration Hub"
        G --> G1[Team Workspaces]
        G --> G2[Comments & Annotations]
        G --> G3[Version Control]
        G --> G4[Sharing & Export]
    end
    
    style A fill:#e1f5fe
    style D fill:#e8f5e8
    style E fill:#f3e5f5
    style F fill:#fff8e1
    style G fill:#fce4ec
```

## Data Processing Pipeline

```mermaid
flowchart TD
    A[Raw Data Input] --> B[Data Profiling]
    B --> C[Quality Assessment]
    C --> D{Data Quality Score}
    
    D -->|High| E[Direct Processing]
    D -->|Medium| F[Cleaning Required]
    D -->|Low| G[Major Transformation]
    
    F --> H[Auto-Cleaning Agent]
    G --> I[Manual Review Required]
    
    H --> J[Validation Check]
    I --> K[User Input for Cleaning]
    K --> J
    
    J --> L{Validation Pass?}
    L -->|No| H
    L -->|Yes| M[Processed Data]
    
    E --> M
    M --> N[Analysis Pipeline]
    M --> O[Visualization Pipeline]
    M --> P[Export Pipeline]
    
    style A fill:#ffebee
    style M fill:#e8f5e8
    style N fill:#e3f2fd
    style O fill:#f3e5f5
    style P fill:#fff3e0
```

## Security & Access Control Flow

```mermaid
flowchart TD
    A[User Access] --> B{Authentication}
    B -->|Valid| C[Authorization Check]
    B -->|Invalid| D[Access Denied]
    
    C --> E{User Role}
    E -->|Admin| F[Full Access]
    E -->|Analyst| G[Analysis + Visualization]
    E -->|Viewer| H[Read Only]
    E -->|Editor| I[Edit + Export]
    
    F --> J[All Features Available]
    G --> K[Analysis Features]
    H --> L[View Only Features]
    I --> M[Edit Features]
    
    J --> N[Audit Logging]
    K --> N
    L --> N
    M --> N
    
    N --> O[Session Management]
    O --> P[Activity Monitoring]
    
    style A fill:#e1f5fe
    style D fill:#ffebee
    style J fill:#e8f5e8
    style N fill:#fff3e0
```
