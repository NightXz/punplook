from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="PunPlook API",
    description="Backend API สำหรับระบบสั่งปลูกล่วงหน้าและติดตามเซ็นเซอร์ IoT - ปันปลูก",
    version="1.0.0"
)

# โครงสร้างข้อมูลสำหรับรับคำสั่งซื้อ (Order-to-Grow)


class OrderRequest(BaseModel):
    crop_name: str = Field(..., example="คะน้าออร์แกนิก")
    quantity_kg: float = Field(..., gt=0, example=2.0)
    unit_price: float = Field(..., gt=0, example=100.0)
    shipping_cost: float = Field(..., ge=0, example=60.0)

# โครงสร้างข้อมูลสำหรับรับค่าจากเซ็นเซอร์ IoT ในแปลงปลูก


class IoTData(BaseModel):
    plot_id: int = Field(..., example=3)
    crop_name: str = Field(..., example="โหระพา")
    soil_moisture: float = Field(..., example=68.0)  # เปอร์เซ็นต์ความชื้น
    temperature: float = Field(..., example=30.0)    # อุณหภูมิเซลเซียส
    soil_ph: float = Field(..., example=5.6)         # ค่าความเป็นกรด-ด่าง


@app.post("/api/orders/calculate-escrow")
def calculate_escrow_payment(order: OrderRequest):
    """
    1. ระบบคำนวณการเงิน Escrow และหักกองทุนความเสี่ยงชุมชน (5%)
    ตามโมเดลเศรษฐกิจแบ่งปันของแพลตฟอร์มปันปลูก
    """
    subtotal = order.quantity_kg * order.unit_price
    total_amount = subtotal + order.shipping_cost

    # หักเข้ากองทุนความเสี่ยงชุมชน 5% ตามเกณฑ์ระบบ
    community_risk_fund = subtotal * 0.05

    # เงินงวดที่ 1 สำหรับเกษตรกร (เช่น 50% ของยอดหลังหักกองทุนสำหรับค่าเมล็ดพันธุ์และปุ๋ย)
    farmer_first_installment = (subtotal - community_risk_fund) * 0.50

    return {
        "status": "success",
        "crop_name": order.crop_name,
        "quantity_kg": order.quantity_kg,
        "subtotal": subtotal,
        "shipping_cost": order.shipping_cost,
        "total_amount_paid": total_amount,
        "breakdown": {
            "community_risk_fund_5_percent": community_risk_fund,
            "farmer_first_installment_30_50_percent": round(farmer_first_installment, 2),
            "escrow_status": "Secured in Escrow"
        }
    }


@app.post("/api/iot/check-soil-status")
def check_soil_status(data: IoTData):
    """
    2. ระบบตรวจสอบสถานะแปลงปลูกจาก IoT Sensors 
    เช่น ตรวจจับค่า pH ดินที่ต่ำกว่าปกติและให้คำแนะนำอัตโนมัติ
    """
    alerts = []
    recommendation = ""

    # เกณฑ์มาตรฐานค่า pH ดินเกษตรอินทรีย์ (ปกติควรอยู่ระหว่าง 6.0 - 7.0)
    if data.soil_ph < 6.0:
        alerts.append(
            f"แปลง {data.plot_id} - pH ต่ำกว่าปกติ (ค่าปัจจุบัน: {data.soil_ph})")
        recommendation = "แนะนำใส่ปูนขาว (Dolomite) 150-200 กรัม/ตร.ม. แล้วรดน้ำทิ้งไว้ 2 วันก่อนวัดซ้ำ"
    elif data.soil_ph > 7.0:
        alerts.append(
            f"แปลง {data.plot_id} - pH สูงกว่าปกติ (ค่าปัจจุบัน: {data.soil_ph})")
        recommendation = "ควรปรับปรุงดินให้อยู่ในภาวะสมดุล"
    else:
        recommendation = "สภาพดินอยู่ในเกณฑ์มาตรฐานเหมาะสมกับการเติบโต"

    return {
        "plot_id": data.plot_id,
        "crop_name": data.crop_name,
        "sensor_readings": {
            "soil_moisture": f"{data.soil_moisture}%",
            "temperature": f"{data.temperature}°C",
            "soil_ph": data.soil_ph
        },
        "system_alert": alerts if alerts else ["สถานะปกติ ไม่มีคำเตือนภัยพิบัติหรือความผิดปกติ"],
        "action_recommendation": recommendation
    }
