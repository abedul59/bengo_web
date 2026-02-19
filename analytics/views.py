from django.shortcuts import render, redirect
from django.contrib import messages
from .models import StockData
import json
from datetime import datetime
import traceback

def dashboard(request):
    # 處理 JSON 上傳
    if request.method == 'POST' and request.FILES.get('json_file'):
        try:
            f = request.FILES['json_file']
            data = json.load(f)
            
            stock_id = data.get('stock_id')
            stock_name = data.get('stock_name')
            history = data.get('history', [])

            # --- 清洗函式保持不變 ---
            def clean_int(v):
                if v is None or v == "": return 0
                try:
                    s = str(v).replace(',', '').strip()
                    f = float(s)
                    return int(f)
                except: return 0

            def clean_float(v):
                if v is None or v == "": return 0.0
                try:
                    return float(str(v).replace(',', '').replace('%', '').strip())
                except: return 0.0
            # -----------------------

            # [關鍵修正]：改用 list 暫存，不直接寫入 DB
            batch_data = []
            
            for row in history:
                d_val = row.get('date')
                d_str = str(d_val).split('.')[0]
                
                try:
                    date_obj = datetime.strptime(d_str, "%Y%m%d").date()
                except ValueError:
                    continue
                
                # 建立物件暫存在記憶體中
                obj = StockData(
                    stock_id=stock_id,
                    stock_name=stock_name,
                    date=date_obj,
                    price=clean_float(row.get('price')),
                    total_shares=clean_int(row.get('total_shares')),
                    total_people=clean_int(row.get('total_people')),
                    bengo_threshold=row.get('threshold_str', ''),
                    major_people=clean_int(row.get('major_ppl')),
                    major_pct=clean_float(row.get('major_pct')),
                    note=row.get('note', '')
                )
                batch_data.append(obj)
            
            # [關鍵修正]：使用 bulk_create 一次性寫入
            # update_conflicts=True 代表：如果資料庫裡已經有這天(stock_id+date)的資料，就更新它 (Upsert)
            if batch_data:
                StockData.objects.bulk_create(
                    batch_data,
                    update_conflicts=True,
                    unique_fields=['stock_id', 'date'],
                    update_fields=[
                        'stock_name', 'price', 'total_shares', 'total_people',
                        'bengo_threshold', 'major_people', 'major_pct', 'note'
                    ]
                )

            messages.success(request, f"極速匯入成功！共處理 {len(batch_data)} 筆資料 ({stock_name})")
            return redirect(f'/?stock={stock_id}')
            
        except Exception as e:
            print(traceback.format_exc())
            messages.error(request, f"匯入錯誤: {e}")

    # --- 查詢邏輯 (保持不變) ---
    query_stock = request.GET.get('stock', '')
    chart_data = {}
    table_data = []
    stock_name_display = ""
    
    if query_stock:
        qs = StockData.objects.filter(stock_id=query_stock).order_by('date')
        if qs.exists():
            stock_name_display = qs.first().stock_name
            chart_data = {
                'dates': [d.date.strftime('%Y/%m/%d') for d in qs],
                'prices': [d.price for d in qs],
                'major_pcts': [d.major_pct for d in qs]
            }
            table_data = qs.order_by('-date')
        else:
            stock_name_display = query_stock

    return render(request, 'dashboard.html', {
        'chart_data': json.dumps(chart_data),
        'table_data': table_data,
        'query_stock': query_stock,
        'stock_name_display': stock_name_display
    })