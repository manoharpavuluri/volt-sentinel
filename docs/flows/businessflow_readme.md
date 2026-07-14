# VoltSentinel Business Flow README

This document explains the end-to-end business process behind VoltSentinel using a renewable-energy agreement between Clearway and a corporate offtaker such as Google.

VoltSentinel is not just a technical lakehouse or RAG demo. It models a real revenue assurance problem in renewable energy: detecting when operational events, ISO/RTO settlements, PPA terms, finance records, and commercial workflow records do not align.

## Business Context

Clearway develops, owns, and operates renewable energy assets such as wind, solar, and storage projects.

A corporate buyer such as Google may sign a long-term Power Purchase Agreement, or PPA, with Clearway to support clean energy goals, data center load, renewable energy credits, and long-term price certainty.

The PPA is typically between:

    Clearway / project company
        <-> Google / corporate offtaker

The ISO/RTO is usually not the PPA customer. The ISO/RTO operates the wholesale market, manages grid reliability, dispatches or curtails resources, calculates market prices, and produces settlement statements.

The ISO/RTO relationship is more like:

    ISO/RTO
        <-> Clearway project company / QSE / scheduling coordinator

## Main Parties

| Party | Role |
|---|---|
| Clearway | Renewable project developer, owner, operator, and seller under the PPA |
| Google | Corporate offtaker / clean energy buyer |
| ISO/RTO | Market operator responsible for grid dispatch, curtailment, prices, and settlements |
| SAP / ERP | Finance system for invoices, GL postings, AR, and payments |
| Salesforce / CRM | Commercial system for accounts, contracts, assets, and disputes |
| VoltSentinel | Revenue assurance layer that detects leakage and prepares evidence-backed cases |

## Core Business Question

The main question is not only whether a renewable asset generated less than expected.

The real business question is:

    Was the asset available to generate?
    Was it curtailed by the ISO/RTO?
    Was the curtailment compensable under the PPA?
    Was the revenue invoiced?
    Was it paid?
    Is there an existing customer dispute?
    What evidence supports the claim?
    Should this become a human-reviewed commercial case?

VoltSentinel is designed to answer that full business workflow.

## End-to-End Business Flow

### 1. Google needs clean energy

Google has data center load and wants long-term clean energy supply, renewable energy credits, carbon-free energy support, and potentially price certainty.

    Google clean energy need
        -> evaluates renewable supply options
        -> negotiates with Clearway
        -> signs PPA / VPPA / energy agreement

### 2. Clearway and Google sign a PPA

The PPA defines the commercial rights and obligations between Clearway and Google.

Typical terms include:

- Project name
- Contract capacity
- Contract term
- Contract price
- Delivery point or settlement point
- Market index
- Renewable energy credit ownership
- Billing terms
- Curtailment rules
- Compensable vs non-compensable curtailment
- Force majeure
- Dispute process
- Credit and payment terms

The PPA answers:

    What should Clearway be paid for?
    What does Google receive?
    How are market prices and contract prices reconciled?
    What happens when the asset is curtailed?

### 3. Clearway develops or operates the project

Clearway develops, builds, acquires, owns, or operates the renewable project through a project company.

    Clearway
        -> project company
        -> wind / solar / storage asset
        -> grid interconnection
        -> commercial operation

Project activities may include:

- Land acquisition or lease
- Permitting
- Interconnection
- Engineering and construction
- Financing
- Market registration
- Operations and maintenance

### 4. Project registers with the ISO/RTO

The renewable asset participates in a wholesale power market such as ERCOT, PJM, SPP, CAISO, or MISO.

The ISO/RTO needs resource information such as:

- Resource ID
- Settlement point
- Meter ID
- Registered market participant
- Scheduling entity / QSE / scheduling coordinator
- Capacity
- Technology type
- Operating limits
- Telemetry
- Interconnection details

Business meaning:

    The PPA defines the commercial contract.
    The ISO/RTO defines how the asset participates in the power market.

### 5. Asset operates daily

On each operating day, the asset produces energy when wind or solar resource is available.

    Weather / wind / solar resource
        -> plant available to generate
        -> SCADA captures expected and actual output
        -> ISO receives telemetry and meter data
        -> ISO dispatches, limits, or curtails output
        -> market price is calculated
        -> settlement is produced

Key operating quantities:

| Term | Meaning |
|---|---|
| Expected available generation | What the plant could have generated |
| Actual generation | What the plant actually injected into the grid |
| Curtailed generation | Available generation that was not accepted or dispatched |
| Market price | ISO/RTO price at the relevant node, hub, or settlement point |
| Settlement quantity | Quantity used by ISO/RTO for financial settlement |

## Example: 100 MW Available, 60 MW Accepted, 40 MW Curtailed

Assume the plant could produce 100 MW in a given hour.

    Plant available capability: 100 MW
    ISO dispatch/basepoint:      60 MW
    Curtailed amount:            40 MW

The ISO/RTO may only accept 60 MW because of:

- Transmission congestion
- Grid reliability constraints
- Local line or substation outage
- Oversupply
- Negative pricing
- Voltage or frequency stability
- Economic dispatch limits

Important distinction:

    100 MW = plant was available
     60 MW = grid/market accepted
     40 MW = curtailed or not dispatched

The 40 MW does not automatically become revenue. Whether it is recoverable depends on the PPA.

## Is Google Physically Getting 100 MW?

Usually, not physically from that plant in that interval.

If the plant only injects 60 MW into the grid, then only 60 MW physically entered the grid from that asset.

In many corporate renewable deals, especially virtual PPAs, Google’s data center is still served by the local grid or retail supplier. Clearway sells the actual energy into the ISO/RTO market, while Clearway and Google settle financially under the PPA.

Virtual PPA style flow:

    Clearway plant
        -> sells actual generated energy into ISO/RTO market

    Google data center
        -> receives physical electricity from grid / utility / retail provider

    Clearway and Google
        -> financially settle under the PPA

So Google may not physically receive the exact electrons from the Clearway plant. The commercial value comes from the financial settlement and renewable attributes.

## ISO/RTO Settlement

The ISO/RTO settles actual market activity.

    ISO/RTO
        <-> Clearway project company / QSE / scheduling coordinator

The ISO/RTO calculates items such as:

- Actual metered MWh
- Market price
- Congestion charges or credits
- Uplift
- Fees
- Adjustments
- Resettlements

Example:

    Actual generated energy: 60 MWh
    Market price:           $30/MWh

    ISO market revenue:
    60 MWh x $30 = $1,800

ISO settlement answers:

    What did the market accept and pay?

## PPA Settlement Between Clearway and Google

The PPA settlement is separate from ISO/RTO settlement.

    Clearway / project company
        <-> Google

The PPA settlement asks:

- What does the contract say Clearway should receive?
- What price applies?
- Does actual generation count?
- Does deemed generation count?
- Is curtailed energy compensable?
- Does Google owe a difference payment?
- Who receives the renewable energy credits?
- Is there a billing or dispute process?

Example:

    PPA price:      $40/MWh
    Market price:   $30/MWh
    Actual output:  60 MWh

If the PPA settles only actual generation:

    Google settlement:
    60 MWh x ($40 - $30) = $600

Clearway total revenue:

    ISO revenue:          $1,800
    Google settlement:      $600
    Total:                $2,400

Which equals:

    60 MWh x $40/MWh

The 40 MWh curtailed amount may or may not be compensated.

## Curtailment Compensation Decision

This is where the business complexity starts.

If the PPA says ISO/RTO-directed curtailment is compensable when the plant was otherwise available, then the 40 MWh may become deemed energy, lost production, or compensable curtailment.

Example:

    Curtailed energy: 40 MWh
    PPA price:        $40/MWh

    Potential compensation:
    40 x $40 = $1,600

If that $1,600 was contractually allowed but never invoiced, disputed, or recovered, it becomes potential revenue leakage.

If the curtailment is non-compensable, then the 40 MWh may not be recoverable.

Non-compensable examples may include:

- Seller-caused outage
- Force majeure
- Excluded economic curtailment
- Negative price periods
- Maintenance outage
- Contractual carve-outs

The key question is:

    Was the curtailed energy contractually recoverable?

## ISO/RTO Documents and Data

The ISO/RTO provides operational and market evidence through market portals, data feeds, settlement systems, APIs, CSV/XML files, EDI, or notices.

Typical ISO/RTO artifacts include:

| Category | Examples | Business Use |
|---|---|---|
| Resource registration | Resource ID, settlement point, market participant setup | Maps asset to market identity |
| Dispatch data | Basepoints, schedules, dispatch instructions | Shows what ISO/RTO accepted |
| Curtailment data | Curtailment notices, constraint instructions | Shows why output was limited |
| Meter data | Revenue meter reads, interval generation | Basis for settlement |
| Price data | LMP, hub price, settlement point price, congestion | Supports revenue calculation |
| Settlement statements | Initial, final, true-up, resettlement statements | Shows ISO-calculated charges and credits |
| Invoices/payment advice | ISO invoice, payment advice, credit notices | Supports cash and accounting reconciliation |
| Dispute records | Settlement disputes, adjustments, resettlement outcomes | Supports correction process |
| Market notices | Rule changes, outage notices, emergency notices | Explains market events and timing |

For the 100/60/40 example, useful ISO/RTO evidence includes:

- Curtailment notice
- Dispatch/basepoint instruction
- Settlement statement
- Metered generation
- Market price
- Constraint reason
- Settlement point
- Resettlement adjustment

## SAP Finance Process

SAP or another ERP represents the finance truth.

    PPA settlement result
        -> customer invoice
        -> invoice line
        -> GL revenue posting
        -> AR open item
        -> payment received
        -> AR cleared

SAP-type records include:

- Customer invoice
- Invoice line
- GL posting
- Revenue account
- AR open item
- Payment status
- Credit memo
- Debit memo
- Adjustment

Business question:

    Was the compensable amount invoiced and paid?

Revenue leakage example:

    Curtailment was compensable under the PPA
    but the customer invoice only reflected actual generation
    and missed the deemed-energy / curtailment compensation amount.

## Salesforce Commercial Process

Salesforce or a similar CRM represents the commercial workflow.

    Customer account
        -> contract
        -> asset/project relationship
        -> dispute/case
        -> approval workflow
        -> customer communication

Salesforce-type records include:

- Account
- Contract
- Asset
- Revenue dispute
- Case
- Approval status
- Commercial owner
- Customer contact

Business question:

    Is there already a dispute?
    Should a new dispute be created?
    Should an existing dispute be updated?
    Who must approve customer-facing action?

## VoltSentinel Revenue Assurance Flow

VoltSentinel combines operational, market, contract, finance, and commercial data.

    SCADA telemetry
      + ISO/RTO curtailment and settlement evidence
      + PPA contract terms
      + SAP invoice/payment records
      + Salesforce account/contract/dispute context
      = case-ready revenue leakage review

VoltSentinel asks:

- Was the asset available?
- Was it curtailed?
- Was the curtailment compensable?
- Was the expected revenue invoiced?
- Was it paid?
- Is there already a dispute?
- What evidence supports the claim?
- Should a human approve next action?

## VoltSentinel Platform Flow

    SCADA telemetry producer
        -> Azure Event Hubs Kafka-compatible stream
        -> Databricks Bronze raw telemetry
        -> Silver cleaned telemetry
        -> Gold revenue leakage fact
        -> Soda quality gate
        -> breach event export
        -> PPA / ISO / settlement evidence linking
        -> SAP finance context
        -> Salesforce commercial context
        -> Gold RAG case package
        -> LangGraph explanation workflow
        -> Databricks RAG result table
        -> human approval queue
        -> mocked Salesforce dispute action

## Full End-to-End Process Flow

    1. Google needs clean energy for data centers
          ↓
    2. Clearway and Google sign PPA / VPPA
          ↓
    3. Clearway develops or operates renewable project
          ↓
    4. Project connects to grid and registers with ISO/RTO
          ↓
    5. Plant generates power when resource is available
          ↓
    6. ISO/RTO dispatches, limits, or curtails generation
          ↓
    7. ISO/RTO records meter data, market prices, and settlement charges/credits
          ↓
    8. Clearway receives ISO/RTO settlement statements and invoices/payment data
          ↓
    9. Clearway calculates PPA settlement with Google
          ↓
    10. SAP creates invoices, GL postings, AR items, and payment records
          ↓
    11. Salesforce tracks customer, contract, asset, and dispute workflow
          ↓
    12. VoltSentinel compares telemetry + ISO/RTO + PPA + SAP + Salesforce
          ↓
    13. Revenue leakage event is identified
          ↓
    14. RAG retrieves contract and settlement evidence
          ↓
    15. AI generates grounded explanation
          ↓
    16. Human reviews and approves
          ↓
    17. Salesforce dispute is created or updated

## Money Flow

    ISO/RTO market settlement:
    ISO/RTO
        <-> Clearway project company / QSE / scheduling coordinator

    PPA settlement:
    Clearway project company
        <-> Google

    Finance settlement:
    Clearway SAP / ERP
        <-> Google AP/payment process

    Commercial workflow:
    Clearway Salesforce / CRM
        <-> Google account/dispute process

Simple example:

    Plant available:          100 MWh
    ISO/RTO accepted:          60 MWh
    Curtailed:                 40 MWh
    Market price:             $30/MWh
    PPA price:                $40/MWh

ISO/RTO market revenue:

    60 x $30 = $1,800

Google PPA actual-generation settlement:

    60 x ($40 - $30) = $600

Potential compensable curtailment:

    40 x $40 = $1,600

If the $1,600 is allowed by the PPA but not invoiced, disputed, or recovered, that becomes potential revenue leakage.

## Data and Document Flow

    SCADA
        -> expected generation
        -> actual generation
        -> availability
        -> outage/curtailment signals

    ISO/RTO
        -> dispatch/basepoint
        -> curtailment notice
        -> meter data
        -> market price
        -> settlement statement
        -> invoice/payment advice

    PPA documents
        -> contract price
        -> curtailment clause
        -> deemed energy formula
        -> billing/dispute process

    SAP
        -> invoice
        -> GL posting
        -> AR open item
        -> payment status

    Salesforce
        -> customer account
        -> contract
        -> asset
        -> dispute/case

    VoltSentinel
        -> leakage calculation
        -> evidence package
        -> RAG explanation
        -> human approval
        -> Salesforce action

## How This Maps to the Current POC

The current VoltSentinel POC implements this business flow using synthetic data and documents.

Implemented components include:

- Synthetic SCADA telemetry producer
- Azure Event Hubs Kafka-compatible ingestion
- Databricks Bronze, Silver, and Gold Delta layers
- Revenue leakage calculation
- Soda Core quality gate
- Synthetic PPA, ISO curtailment notice, and settlement documents
- Synthetic SAP invoice, GL, AR, and asset records
- Synthetic Salesforce account, contract, asset, and dispute records
- Gold case-ready revenue leakage package
- LangGraph RAG explanation workflow
- Databricks RAG result persistence
- Human approval queue
- Mocked Salesforce dispute action

## Interview Explanation

In a Clearway-Google type agreement, Google is the commercial offtaker under the PPA, while the ISO/RTO operates the wholesale market where the renewable asset is dispatched and settled.

If the asset is capable of producing 100 MW but the ISO/RTO only accepts 60 MW because of congestion or reliability constraints, the remaining 40 MW may be curtailed. Whether that 40 MW is recoverable depends on the PPA's curtailment language.

The ISO/RTO settlement shows what the market paid. SAP shows what was invoiced and collected. Salesforce shows the customer, contract, and dispute workflow. The PPA and ISO/RTO documents explain whether the lost production is compensable.

VoltSentinel brings these pieces together to detect possible revenue leakage and prepare a human-reviewed, evidence-backed dispute case.
