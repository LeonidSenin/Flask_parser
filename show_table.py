from flask import Blueprint, render_template
from forms import TableFrom
import pandas as pd

app2_blueprint = Blueprint('app2', __name__)

@app2_blueprint.route('/table')
def dash_table():
    form = TableFrom()
    df = pd.read_pickle('table_show.pkl')
    table = df.to_html(render_links=True, index=False, classes='mystyle', escape=False)
    return render_template('table.html', title='Таблица', form=form, table=table)