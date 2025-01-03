from dash import Dash, dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.graph_objects as go
import pandas as pd
import locale

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# Initialize the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.MATERIA])
app.title = "Salary Planner"


# import data

tax = pd.read_csv("https://raw.githubusercontent.com/umaurosli/Python-Projects/refs/heads/main/Salary-Dashboard/Raw%20File/Tax%20Deduction%20Table.csv")
sosco_eis=pd.read_csv("https://raw.githubusercontent.com/umaurosli/Python-Projects/refs/heads/main/Salary-Dashboard/Raw%20File/socso%20and%20eis%20deduction%20table.csv")


# Layout of the app
app.layout = dbc.Container(
    [
        html.H1("Salary Planner", className="text-center my-1"),
        html.H2("created by Umar Rosli", style={'font-size': '11px', 'text-align': 'center','margin-top':'0px'}),
        
        # Input Form
        dbc.Row(
            [
                dbc.Col([
                    html.H3("Salary information", style={'font-size': '18px'}),
                    html.Div(style={'height': '10px'}),
                    html.Label("Monthly Salary", style={'font-size': '16px'}),
                    dbc.Input(type="number", id="monthly-salary", placeholder="Enter salary in RM", style={'font-size': '14px'}),
                    html.Br(),
                    
                    html.Label("Status"),
                    dcc.Dropdown(
                        id="status-dropdown",
                        options=[
                            {"label": "Single", "value": "single"},
                            {"label": "Married (Spouse Not Working)", "value": "married_no"},
                            {"label": "Married (Spouse Working)", "value": "married_yes"},
                        ],
                        placeholder="Select status",
                    ),
                    html.Br(),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label("Allowances", style={'font-size': '16px'}),
                            dbc.Input(type="number", id="allowances", placeholder="Enter allowances", style={'font-size': '14px', 'width': '90%'}),
                        ], width=6),
                        dbc.Col([
                            html.Label("Bonuses", style={'font-size': '16px'}),
                            dbc.Input(type="number", id="bonuses", placeholder="Enter bonuses", style={'font-size': '14px', 'width': '90%'}),
                        ], width=6),
                    ]),
                    html.Br(),

                    dbc.Row([
                        dbc.Col([
                            html.Label("Age Segment", style={'font-size': '16px'}),
                            dbc.Row([
                                dbc.Col([
                                    html.Div(style={'height': '10px'}),
                                    daq.BooleanSwitch(id="age-segment", on=True)
                                ],width=5),
                                dbc.Col([
                                    html.Div(style={'height': '10px'}),
                                    html.Div(id="age-segment-label", className="mr-2", style={'font-size': '14px'}) # Label that updates dynamically
                                ],width=7)
                            ]),
                        ]),

                        dbc.Col([
                            html.Label("EPF Rate (%)", style={'font-size': '16px'}),
                            dbc.Input(type="number", id="epf-rate", placeholder="Enter EPF rate"),
                        ],width=6)
                    ]),
                    html.Br(),
                    
                    dbc.Button("Calculate", id="calculate-btn", className="mt-3", color="primary"),
                ], width=5),
                
                # Results Area
                dbc.Col([
                    html.H4("Results"),
                    html.Div(id="results-table"),  # Placeholder for table
                    dcc.Graph(id="results-graph"),  # Placeholder for graph
                    html.Div(id="annual-table"),  # Placeholder for annual insights table
                ], width=7),
            ],
            className="my-4",
        ),
    ],
    fluid=True,
)

# Callback to update the age segment label dynamically
@app.callback(
    Output("age-segment-label", "children"),
    Input("age-segment", "on")
)
def update_age_segment_label(is_on):
    return "Above 60 years" if is_on else "Below 60 years"

# Callback to perform calculations and update outputs
@app.callback(
    [
        Output("results-table", "children"),
        Output("results-graph", "figure"),
        Output("annual-table", "children"),
    ],
    [Input("calculate-btn", "n_clicks")],
    [
        State("monthly-salary", "value"),
        State("allowances", "value"),
        State("bonuses", "value"),
        State("epf-rate", "value"),
        State("status-dropdown", "value"),
    ]
)
def update_results(n_clicks, salary, allowances, bonuses, epf_rate, marital_status):
    if n_clicks and salary and epf_rate:
        # Placeholder calculations (to be replaced with actual logic)
        gross_salary = salary + (allowances or 0) + (bonuses or 0)

        #EPF Deduction
        epf_deduction = (epf_rate / 100) * salary

        #Deduction EIS, SOCSO
        filtered_deduction = sosco_eis[(salary > sosco_eis['Gaji Awal']) & (salary <= sosco_eis['Gaji Akhir'])]
        eis_deduction = filtered_deduction['Kadar Caruman EIS'].iloc[0]
        socso_deduction = filtered_deduction['Kadar Caruman SOCSO'].iloc[0]

        # Monthly PCB Deduction

        gross_annual_salary = salary*12
        annual_salary_deducted = gross_annual_salary - 13000

        if marital_status == "married_no":
            annual_salary_deducted = annual_salary_deducted - 4000

        filtered_taxed_salary = tax[(annual_salary_deducted > tax['Julat Awal Gaji']) & (annual_salary_deducted <= tax['Julat Akhir Gaji'])]
        
        first_layer_tax = filtered_taxed_salary['Kadar Cukai Lapisan Pertama'].iloc[0]
        second_layer_salary = annual_salary_deducted-filtered_taxed_salary['Kadar Gaji Lapisan Pertama'].iloc[0]
        second_layer_percent = filtered_taxed_salary['Kadar Cukai Lapisan Kedua'].iloc[0]
        second_layer_tax = second_layer_salary*second_layer_percent

        if marital_status == "married-no":
            special_rebate = filtered_taxed_salary['Kadar Rebat Cukai Tahunan (B)'].iloc[0]
        else:
            special_rebate = filtered_taxed_salary['Kadar Rebat Cukai Tahunan (A & C)'].iloc[0]
        
        annual_tax = (first_layer_tax+second_layer_tax)-special_rebate
        monthly_tax = annual_tax/12

        total_deductions = epf_deduction + eis_deduction + socso_deduction + monthly_tax # Add SOCSO, EIS, PCB tax here
        net_salary = gross_salary - total_deductions
        
        # Results table
        results_df = pd.DataFrame({
            "Category": ["Gross Salary", "EPF Deduction", "EIS Deduction", "SOCSO Deduction", "Monthly PCB", "Net Salary"],
            "Amount (RM)": [gross_salary, epf_deduction, eis_deduction, socso_deduction, monthly_tax, net_salary],
        })
        results_df["Amount (RM)"] = results_df["Amount (RM)"].apply(lambda x: locale.format_string("%.2f", x, grouping=True))
        results_table = dash_table.DataTable(
            data=results_df.to_dict("records"),
            columns=[{"name": i, "id": i} for i in results_df.columns],
            style_table={"width": "100%", "margin": "auto"},
        )

        # Pie chart
        pie_chart = go.Figure(
            data=[
                go.Pie(
                    labels=["Net Salary", "Total Deductions"],
                    values=[net_salary, total_deductions],
                    hole=0.4,
                    hovertemplate="%{label}: RM %{value:,.2f}<extra></extra>",
                )
            ]
        )
        pie_chart.update_layout(title="Salary Distribution")

        # Annual insights table
        annual_df = pd.DataFrame({
            "Category": ["Gross Annual Income", "Net Annual Income", "Total Annual Deductions"],
            "Amount (RM)": [gross_salary * 12, net_salary * 12, total_deductions * 12],
        })
        annual_df["Amount (RM)"] = annual_df["Amount (RM)"].apply(lambda x: locale.format_string("%.2f", x, grouping=True))
        annual_table = dash_table.DataTable(
            data=annual_df.to_dict("records"),
            columns=[{"name": i, "id": i} for i in annual_df.columns],
            style_table={"width": "100%", "margin": "auto"},
        )

        return results_table, pie_chart, annual_table

    return None, go.Figure(), None

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
