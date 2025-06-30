import plotly.graph_objects as go
from plotly.offline import plot
from collections import defaultdict
import pandas as pd
from datetime import date,datetime

def generate_bar_chart(expenses):
    data = defaultdict(int)
    for e in expenses:
        data[e.name] += e.amount

    names = list(data.keys())
    amounts = list(data.values())

    bar = go.Bar(x=names,y=amounts,marker_color = "cyan")
    layout = go.Layout(title= 'Expenses by Name',
                       height=400,
                        xaxis=dict(title='Name'),
                        yaxis=dict(title='Amount'),
                        paper_bgcolor='#1a3d63',
                        plot_bgcolor='#1a3d63',
                        font=dict(color='white'))
                    #    paper_bgcolor='#1a3d63')
    fig = go.Figure(data=[bar],layout=layout)

    return plot(fig,output_type='div', include_plotlyjs = False)

def generate_pie_chart(expenses):
    from plotly.offline import plot
    from collections import defaultdict
    import plotly.graph_objects as go

    data = defaultdict(int)
    for e in expenses:
        data[e.name] += e.amount

    labels = list(data.keys())
    values = list(data.values())

    pie = go.Pie(
        labels=labels,
        values=values,
        hole=0.4,  # ✅ Makes it a donut
        textinfo='label+percent',
        insidetextorientation='radial',
        marker=dict(line=dict(color='white', width=1))
    )

    layout = go.Layout(
        title='Expense Distribution',
        paper_bgcolor='#1a3d63',
        plot_bgcolor='#1a3d63',
        font=dict(color='white'),
    )

    fig = go.Figure(data=[pie], layout=layout)
    return plot(fig, output_type='div', include_plotlyjs=False)



def generate_worm_chart(expenses):
    # Filter valid dates
    valid_expenses = [e for e in expenses if isinstance(e.date, date) and e.date.year > 1900]
    if not valid_expenses:
        return "<div>No valid data to display.</div>"

    # Create DataFrame
    df = pd.DataFrame({
        'date': [e.date for e in valid_expenses],
        'amount': [float(e.amount) for e in valid_expenses]
    })

    df['year'] = df['date'].apply(lambda d: int(d.year))
    grouped = df.groupby('year', as_index=False)['amount'].sum()

    # Debug
    print("DEBUG - Final Grouped Data:")
    print(grouped)

    # Create Scatter trace
    trace = go.Scatter(
        x=grouped['year'],
        y=grouped['amount'],
        mode='lines+markers',  # shows both worm and dots
        line=dict(shape='linear', color='lime', width=3),
        marker=dict(size=10, color='cyan', line=dict(width=1, color='black')),
        hovertemplate='Year: %{x}<br>Amount: ₹%{y:,.0f}<extra></extra>',
        name='Annual Expenses'
    )

    layout = go.Layout(
    title=dict(
        text='Total Expenses Per Year',
        x=0.5,
        xanchor='center',
        pad=dict(t=0, b=0)
    ),
    autosize=True,
    height=200,
    margin=dict(l=50, r=40, t=30, b=50),

    xaxis=dict(
        title=dict(
            text='Year',
            font=dict(color='white')
        ),
        type='linear',
        tickmode='linear',
        dtick=1,
        tickfont=dict(size=10, color='white'),
        showgrid=True,
        gridcolor='rgba(255, 255, 255, 0.12)',
        gridwidth=1,
        zeroline=True,
        zerolinecolor='white',
        zerolinewidth=2,
        linecolor='white',
        linewidth=2
    ),

    yaxis=dict(
        title=dict(
            text='Amount (₹)',
            font=dict(color='white')
        ),
        tickformat=',',
        tickfont=dict(size=10, color='white'),
        range=[0, grouped['amount'].max() * 1.2],
        showgrid=True,
        gridcolor='rgba(255, 255, 255, 0.12)',
        gridwidth=1,
        zeroline=True,
        zerolinecolor='white',
        zerolinewidth=2,
        linecolor='white',
        linewidth=2
    ),

    paper_bgcolor='#1a3d63',
    plot_bgcolor='#1a3d63',
    font=dict(color='white')
)
    fig = go.Figure(data=[trace], layout=layout)
    return plot(fig, output_type='div', include_plotlyjs=False)



def create_gauge(title, value, budget_limit=50000, width=150, height=150, ref=None, show_budget=False):
    # Subtitle for budget difference
    subtitle = ""
    if show_budget:
        diff = value - budget_limit
        used_pct = (value / budget_limit) * 100 if budget_limit else 0
        if diff > 0:
            subtitle = f"<br><span style='font-size:11px;color:red;'>📈 ₹{diff:,.0f} over ({used_pct:.1f}%)</span>"
        else:
            subtitle = f"<br><span style='font-size:11px;color:lime;'>📉 ₹{abs(diff):,.0f} under ({used_pct:.1f}%)</span>"

    title_html = f"<b>{title}</b>{subtitle}"

    # Filled color logic
    bar_color = "lime" if value <= budget_limit else "red"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta" if ref is not None else "gauge+number",
        value=value,
        delta={
            "reference": ref,
            "increasing": {"color": "red", "symbol": "▲"},
            "decreasing": {"color": "lime", "symbol": "▼"},
            "valueformat": ","
        } if ref is not None else None,
        title={'text': title_html, 'font': {'size': 13, 'color': 'white'}},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 50000], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': bar_color, 'thickness': 0.35},
            'bgcolor': "white",  # makes the unfilled part white bordered
            'steps': [],  # no gradient fill in background
            'threshold': {
                'line': {'color': "white", 'width': 2},
                'thickness': 0.75,
                'value': budget_limit
            } if show_budget else None
        }
    ))

    fig.update_layout(
        paper_bgcolor="#1a3d63",
        plot_bgcolor="#1a3d63",
        font=dict(color="white"),
        margin=dict(t=50, b=20, l=10, r=10),
        width=width,
        height=height
    )

    return plot(fig, output_type='div', include_plotlyjs=False)


def generate_gauge_charts(expenses, monthly_budget_limit=5000):
    now = datetime.now()
    df = pd.DataFrame([{
        'name': e.name,
        'amount': e.amount,
        'date': e.date
    } for e in expenses if e.date.year >= now.year - 1])

    if df.empty:
        return "<div>No gauge data available.</div>", "", ""

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df.dropna(subset=['date'], inplace=True)
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year

    curr_month = df[(df['year'] == now.year) & (df['month'] == now.month)]['amount'].sum()
    last_month = df[(df['year'] == now.year) & (df['month'] == now.month - 1)]['amount'].sum()
    curr_year = df[df['year'] == now.year]['amount'].sum()

    # ✅ 1. Large gauge for "This Month" WITH budget
    gauge_this_month = create_gauge("This Month", curr_month, monthly_budget_limit,
                                    width=386, height=170, show_budget=True)

    # ✅ 2. Small gauge for "This Year" (no budget)
    gauge_this_year = create_gauge("This Year", curr_year, curr_year,
                                   width=180, height=140, show_budget=False)

    # ✅ 3. Small gauge for "Month vs Last"
    gauge_month_vs_last = create_gauge("Month vs Last", curr_month,
                                       max(curr_month, last_month, 10000),
                                       width=180, height=140,
                                       ref=last_month,
                                        show_budget=False)

    return gauge_this_month, gauge_this_year, gauge_month_vs_last


def generate_sparkline(expenses):
    df = pd.DataFrame([{
        'amount': e.amount,
        'date': e.date
    } for e in expenses])

    if df.empty:
        return "<div>No data for sparkline.</div>"

    df['date'] = pd.to_datetime(df['date'])
    df.sort_values('date', inplace=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['amount'],
        mode='lines+markers',
        line=dict(color='lime', width=2),
        marker=dict(size=4),
        hovertemplate='%{x|%b %d, %Y}<br>₹%{y}<extra></extra>'
    ))

    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=100,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, showticklabels=False),
    )

    return plot(fig, output_type='div', include_plotlyjs=False)


def get_icon_status_data(expenses, monthly_budget=25000):
    from collections import Counter
    from datetime import datetime

    now = datetime.now()
    this_month_exp = [e for e in expenses if e.date.month == now.month and e.date.year == now.year]
    total_spent = sum(e.amount for e in this_month_exp)
    num_txns = len(this_month_exp)
    daily_avg = round(total_spent / now.day, 2) if now.day else 0

    # Top category this month
    cat_counter = Counter(e.name for e in this_month_exp)
    top_category = cat_counter.most_common(1)
    top_cat_name = top_category[0][0] if top_category else "N/A"
    top_cat_total = sum(e.amount for e in this_month_exp if e.name == top_cat_name)

    budget_diff = total_spent - monthly_budget
    budget_status = f"₹{abs(budget_diff):,.0f} {'over 🔴' if budget_diff > 0 else 'under 🟢'}"
    # Most frequently used category (by count)
    most_freq_cat = cat_counter.most_common(1)
    freq_cat_name = most_freq_cat[0][0] if most_freq_cat else "N/A"
    freq_cat_count = most_freq_cat[0][1] if most_freq_cat else 0

    return [
        {"icon": "💰", "label": "Total This Month", "value": f"₹{total_spent:,.0f}"},
        {"icon": "📊", "label": "Daily Avg", "value": f"₹{daily_avg:,.0f}/day"},
        {"icon": "🧊", "label": "Transactions", "value": f"{num_txns}"},
        {"icon": "📈", "label": "Top Category", "value": f"{top_cat_name}: ₹{top_cat_total:,.0f}"},
        {"icon": "🎯", "label": "Budget Status", "value": budget_status},
        {"icon": "🔁", "label": "Most Frequent", "value": f"{freq_cat_name} ({freq_cat_count}×)"}
    ]
