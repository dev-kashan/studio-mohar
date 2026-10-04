def generate_order_zip_file(order):
    from datetime import timedelta
    from io import BytesIO
    import zipfile
    import os
    from PIL import Image
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from shop.models import Layout  # Import Layout model

    buffer = BytesIO()
    zip_file = zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED)
    base_folder = f"{order.Order_number}"

    # ================= PDF INVOICE =================
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    width, height = A4

    # Color Scheme
    PRIMARY_COLOR = colors.HexColor("#7E9479")
    ACCENT_COLOR = colors.HexColor("#7E9479")
    LIGHT_GRAY = colors.HexColor("#f8f9f8")
    DARK_GRAY = colors.HexColor("#5a5a5a")
    WHITE = colors.white
    BLACK = colors.black

    # ---------- LOGO & COMPANY HEADER ----------
    from django.conf import settings

    y = height - 35
    logo_height = 120
    logo_x = 40

    try:
        layout = Layout.objects.first()
        logo_path = None
        if layout and layout.logo:
            if hasattr(layout.logo, 'path') and os.path.exists(layout.logo.path):
                logo_path = layout.logo.path
            else:
                from django.conf import settings
                import os
                potential_path = os.path.join(settings.MEDIA_ROOT, str(layout.logo))
                if os.path.exists(potential_path):
                    logo_path = potential_path

        if logo_path:
            # Adjust logo Y so its center aligns with text Y
            logo_y = y - (logo_height / 2)
            c.drawImage(
                logo_path,
                logo_x,
                logo_y,
                width=logo_height,  # square logo
                height=logo_height,
                preserveAspectRatio=True,
                mask='auto'
            )
        else:
            raise Exception("No valid logo")

    except Exception:
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(PRIMARY_COLOR)
        c.drawString(logo_x + 2, y - 8, "SM")


    # Company branding
    # c.setFont("Helvetica-Bold", 18)
    # c.setFillColor(PRIMARY_COLOR)
    # c.drawString(logo_x + 40, y, "Studio Mohar")

    # c.setFont("Helvetica", 9)
    # c.setFillColor(DARK_GRAY)
    # c.drawString(logo_x + 40, y - 12, "Ruii Textile Inc")

    # Invoice title and number on the right
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(ACCENT_COLOR)
    c.drawRightString(width - 40, y, "INVOICE")

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(DARK_GRAY)
    c.drawRightString(width - 40, y - 16, f"#{order.Order_number}")

    # Decorative line
    y -= 40
    c.setLineWidth(2)
    c.setStrokeColor(ACCENT_COLOR)
    c.line(40, y, width - 40, y)

    # ---------- BILL TO & SHIP TO SECTION ----------
    y -= 20

    # SHIP To section
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(PRIMARY_COLOR)
    c.drawString(40, y, "SHIP TO")

    c.setFont("Helvetica", 9)
    c.setFillColor(BLACK)
    y -= 14
    c.drawString(40, y, order.name)
    y -= 11
    c.drawString(40, y, order.address)
    y -= 11
    c.drawString(40, y, order.city)
    y -= 11
    c.drawString(40, y, f"Phone: {order.phone}")
    y -= 11
    c.drawString(40, y, f"Email: {order.email}")
    y -= 11
    c.drawString(40, y, f"Postal Code: {order.zip_code}")
    y -= 11
    c.drawString(40, y, f"Province: {order.province.name}")

    # Ship To section (right side)
    # ship_x = width - 260
    # ship_y = height - 115
    # c.setFont("Helvetica-Bold", 11)
    # c.setFillColor(PRIMARY_COLOR)
    # c.drawString(ship_x, ship_y, "SHIP TO")

    # c.setFont("Helvetica", 9)
    # c.setFillColor(BLACK)
    # ship_y -= 14
    # c.drawString(ship_x, ship_y, "Same as Billing")

    # ---------- INVOICE DETAILS (Left Column below Bill To) ----------
    y -= 30  # Add spacing after Bill To section
    
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(DARK_GRAY)
    c.drawString(40, y, "Order Date:")
    c.setFont("Helvetica", 9)
    c.setFillColor(BLACK)
    c.drawString(120, y, f"{order.created.strftime('%b %d, %Y')}")

    y -= 20
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(DARK_GRAY)
    c.drawString(40, y, "Payment Terms:")
    c.setFont("Helvetica", 9)
    c.setFillColor(BLACK)
    c.drawString(120, y, "Pay in full")

    # y -= 20
    # c.setFont("Helvetica-Bold", 9)
    # c.setFillColor(DARK_GRAY)
    # c.drawString(40, y, "Due Date:")
    # c.setFont("Helvetica", 9)
    # c.setFillColor(BLACK)
    # c.drawString(100, y, f"{(order.created + timedelta(days=4)).strftime('%b %d, %Y')}")

    # Shipping information
    shipping_type = getattr(order, 'ship_type', 'Standard Shipping')
    estimated_shipping_date = getattr(order, 'estimated_delivery_time', order.created + timedelta(days=5))

    y -= 20
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(DARK_GRAY)
    c.drawString(40, y, "Shipping Type:")
    c.setFont("Helvetica", 9)
    c.setFillColor(BLACK)
    c.drawString(120, y, str(shipping_type))

    y -= 20
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(DARK_GRAY)
    c.drawString(40, y, "Est. Ship Date:")
    c.setFont("Helvetica", 9)
    c.setFillColor(BLACK)
    if hasattr(estimated_shipping_date, 'strftime'):
        c.drawString(120, y, estimated_shipping_date.strftime('%b %d, %Y'))
    else:
        c.drawString(120, y, str(estimated_shipping_date))

    # ---------- TABLE HEADER ----------
    y -= 40  # Increased spacing before table to prevent overlap
    table_header_y = y
    header_height = 22

    # Header background with gradient effect (dark color)
    c.setFillColor(PRIMARY_COLOR)
    c.rect(40, y - header_height, width - 80, header_height, fill=1)

    # Header text
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y - 15, "Item (Size)")
    c.drawString(310, y - 15, "Qty")
    c.drawString(380, y - 15, "Rate")
    c.drawString(475, y - 15, "Amount")

    y -= (header_height + 5)
    c.setFont("Helvetica", 9)
    c.setFillColor(BLACK)

    # ---------- ITEMS ----------
    items = list(order.orderitem_set.all())
    row_height = 22
    subtotal = 0
    alternate_row = False

    for idx, item in enumerate(items):
        for size_obj in item.sizes.all():
            if y < 130:
                c.showPage()
                y = height - 40

            # Alternate row colors for better readability
            if alternate_row:
                c.setFillColor(LIGHT_GRAY)
                c.rect(40, y - row_height, width - 80, row_height, fill=1)
                c.setFillColor(BLACK)

            qty = size_obj.quantity
            rate = float(size_obj.unit_price)
            amount = qty * rate
            subtotal += amount

            name = f"{item.product_name} ({size_obj.size})"
            if len(name) > 45:
                name = name[:45] + "..."

            c.setFont("Helvetica", 9)
            c.drawString(50, y - 14, name)
            c.drawString(310, y - 14, str(qty))
            c.drawString(380, y - 14, f"CA${rate:.2f}")
            c.drawRightString(width - 50, y - 14, f"CA${amount:.2f}")

            y -= row_height
            alternate_row = not alternate_row

    # ---------- TOTALS SECTION ----------

    tax_amount = float(order.tax or 0)
    main_subtotal = float(order.SubTotal or 0)
    discount = float(order.discount_amount or 0)
    delivery = float(order.Delivery or 0)
    total_amount = float(order.total or 0)

    y -= 30

    # Totals container with proper spacing
    totals_box_x = width - 300
    totals_box_width = 260
    totals_left = totals_box_x + 20
    totals_right = totals_box_x + totals_box_width - 20

    # Subtotal line
    c.setFont("Helvetica", 10)
    c.setFillColor(BLACK)
    c.drawString(totals_left, y, "Subtotal:")
    c.drawRightString(totals_right, y, f"CA${main_subtotal:.2f}")

    # Tax line
    y -= 18
    c.setFont("Helvetica", 10)
    c.setFillColor(BLACK)
    c.drawString(totals_left, y, "Tax:")
    c.drawRightString(totals_right, y, f"CA${tax_amount:.2f}")

    # Discount line (if applicable)
    if delivery:
        y -= 18
        c.setFont("Helvetica", 10)
        c.setFillColor(BLACK)
        c.drawString(totals_left, y, "Delivery:")
        c.drawRightString(totals_right, y, f"CA${delivery:.2f}")
    if discount:
        y -= 18
        c.setFont("Helvetica", 10)
        c.setFillColor(BLACK)
        c.drawString(totals_left, y, "Discount:")
        c.drawRightString(totals_right, y, f"-CA${discount:.2f}")

    # Total line with highlight
    y -= 22
    c.setLineWidth(2)
    c.setStrokeColor(ACCENT_COLOR)
    c.setFillColor(ACCENT_COLOR)
    c.rect(totals_box_x, y - 20, totals_box_width, 24, fill=0)

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(ACCENT_COLOR)
    c.drawString(totals_left, y - 12, "Total:")
    c.drawRightString(totals_right, y - 12, f"CA${total_amount:.2f}")

    # Balance Due
    # y -= 28
    # c.setFont("Helvetica-Bold", 11)
    # c.setFillColor(PRIMARY_COLOR)
    # c.drawString(40, y, "Balance Due:")

    # c.setFont("Helvetica-Bold", 11)
    # c.setFillColor(BLACK)
    # c.drawString(130, y, f"CA${total_amount:.2f}")

    # ---------- SPECIAL INSTRUCTIONS ----------
    if order.special_instructions:
        y -= 40
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(PRIMARY_COLOR)
        c.drawString(40, y, "SPECIAL INSTRUCTIONS")

        c.setFont("Helvetica", 9)
        c.setFillColor(BLACK)
        y -= 14
        text = c.beginText(40, y)
        text.fontSize = 8
        for line in order.special_instructions.split("\n"):
            text.textLine(line)
        c.drawText(text)

    c.showPage()
    c.save()

    zip_file.writestr(f"{base_folder}/order_summary.pdf", pdf_buffer.getvalue())

    # ================= ITEM FILES =================
    for idx, item in enumerate(items, start=1):
        item_folder = f"{base_folder}/Item_{idx}_{item.product_name.replace(' ', '_')}"

        details = [
            f"Product: {item.product_name}",
            f"Color: {item.color}",
            # f"Unit Price: {item.unity_price}",
            f"Order Type: {item.Order_Type}",
            f"Status: {item.status}",
            "",
            "Sizes Ordered:"
        ]

        for size_obj in item.sizes.all():
            price_each = getattr(size_obj, 'unit_price', 0)  # or however you store price
            total_price = getattr(size_obj, 'total_price', 0)  # or however you store price
            details.append(
                f"{size_obj.size} ({size_obj.quantity}) x C${price_each:.2f} = C${total_price:.2f}"
            )

        def add_image(field, path):
            if field and getattr(field, "name", None):
                try:
                    zip_file.writestr(path, field.read())
                except Exception:
                    pass

        add_image(item.Front_Image, f"{item_folder}/mockups/front.png")
        add_image(item.Back_Image, f"{item_folder}/mockups/back.png")
        add_image(item.Left_Image, f"{item_folder}/mockups/left.png")
        add_image(item.Right_Image, f"{item_folder}/mockups/right.png")

        add_image(item.Front_Desgin_Image, f"{item_folder}/designs_hd/front.png")
        add_image(item.Back_Desgin_Image, f"{item_folder}/designs_hd/back.png")
        add_image(item.Left_Desgin_Image, f"{item_folder}/designs_hd/left.png")
        add_image(item.Right_Desgin_Image, f"{item_folder}/designs_hd/right.png")

        user_folder = f"{item_folder}/user_uploaded_images"
        for uploaded in item.uploaded_files.all():
            zip_file.writestr(
                f"{user_folder}/{uploaded.filename or os.path.basename(uploaded.file.name)}",
                uploaded.file.read()
            )

        zip_file.writestr(f"{item_folder}/item_details.txt", "\n".join(details))

    zip_file.close()
    buffer.seek(0)
    return buffer