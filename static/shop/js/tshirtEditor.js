var canvas;
var tshirts = new Array(); //prototype: [{style:'x',color:'white',front:'a',back:'b',price:{tshirt:'12.95',frontPrint:'4.99',backPrint:'4.99',total:'22.47'}}]
var a;
var b;
var c;
var d;
var line1;
var line2;
var line3;
var line4;
let currentView = "front"; // default

window.uploadedDesignFiles = {
    front: [],
    back: [],
    left_sleeve: [],
    right_sleeve: []
};


// store original base price ONCE when the page loads
let baseProductPrice = parseFloat($(".dynamic_price_total").text()) || 0;
// let designCostPerItem  = 0


let designedSides = {
  front: { designed: false, embroidery: false },
  back: { designed: false, embroidery: false },
  left_sleeve: { designed: false, embroidery: false },
  right_sleeve: { designed: false, embroidery: false },
};


const designPrices = {
    front: parseFloat(document.getElementById("price_front").value) || 0,
    back: parseFloat(document.getElementById("price_back").value) || 0,
    left_sleeve: parseFloat(document.getElementById("price_left_sleeve").value) || 0,
    right_sleeve: parseFloat(document.getElementById("price_right_sleeve").value) || 0,
    embroidery_extra: parseFloat(document.getElementById("price_embroidery_extra").value) || 0,
};

console.log("okkkkkkkk", designPrices);



window.onload = function () {
    const canvasEl = document.getElementById('tcanvas');
    canvasEl.width = canvasEl.offsetWidth;
    canvasEl.height = canvasEl.offsetHeight;

    const canvas = new fabric.Canvas('tcanvas', {
        hoverCursor: 'pointer',
        selection: true,
        selectionBorderColor: 'blue',
    });

    // Optional: increase pixel density for retina screens
    // canvas.setZoom(window.devicePixelRatio || 1);

    

function resizeCanvas() {
  const container = document.querySelector('.canvas-container');
  const width = container.clientWidth;
  const height = container.clientHeight;

  canvas.setWidth(width);
  canvas.setHeight(height);
  canvas.renderAll();
}

// resizeCanvas();
// window.addEventListener('resize', resizeCanvas);

document.addEventListener('mousedown', function (e) {
    const canvasElement = canvas.getElement();

    const drawingArea = document.getElementById('drawingArea');
    const appearancePanel = document.querySelector('.apparance_panel'); // your side panel

    // if clicked outside canvas AND clicked outside appearance_panel then unselect
    if (!drawingArea.contains(e.target) && !appearancePanel.contains(e.target)) {
        canvas.discardActiveObject();
        canvas.requestRenderAll();
    }
});


    canvas.on('object:moving', function (e) {
        var obj = e.target;

        // Get canvas boundaries
        var canvasWidth = canvas.width;
        var canvasHeight = canvas.height;

        // Object dimensions (scaled)
        var objWidth = obj.getScaledWidth();
        var objHeight = obj.getScaledHeight();

        // Restrict X (left/right)
        if (obj.left < 0) {
            obj.left = 0;
        }
        if (obj.left + objWidth > canvasWidth) {
            obj.left = canvasWidth - objWidth;
        }

        // Restrict Y (top/bottom)
        if (obj.top < 0) {
            obj.top = 0;
        }
        if (obj.top + objHeight > canvasHeight) {
            obj.top = canvasHeight - objHeight;
        }
    });

    let layerIdCounter = 0;


    // 		let a = null; // front json
    // let b = null; // back json

    // load front design first if available
// First: detect which sides were previously designed
if (window.savedDesign) {

        // ✅ Ensure all sides exist in designedSides
        if (!designedSides.front) designedSides.front = {};
        if (!designedSides.back) designedSides.back = {};
        if (!designedSides.left) designedSides.left = {};
        if (!designedSides.right) designedSides.right = {};

        // ✅ Mark designed sides based on saved JSON
        designedSides.front.designed = !!window.savedDesign.front && window.savedDesign.front !== "";
        designedSides.back.designed = !!window.savedDesign.back && window.savedDesign.back !== "";
        designedSides.left.designed = !!window.savedDesign.left_sleeve && window.savedDesign.left_sleeve !== "";
        designedSides.right.designed = !!window.savedDesign.right_sleeve && window.savedDesign.right_sleeve !== "";

        // ✅ Update total pricing immediately
        updateSidePricing();

        // ✅ Load front canvas visually
        if (window.savedDesign.front) {
            canvas.loadFromJSON(window.savedDesign.front, function () {
                canvas.renderAll();

                // Clear layers list and rebuild
                $("#layersList").empty();
                canvas.getObjects().forEach(obj => {
                    let type = (obj.type === "text" || obj.type === "i-text" || obj.type === "textbox")
                        ? "textbox"
                        : "image";
                    if (!obj.layerId) obj.layerId = "layer_" + (++layerIdCounter);
                    addDeleteControl(obj);
                    addLayerToList(obj, type);
                });

                // Mark front as designed if it has objects
                if (canvas.getObjects().length > 0) {
                    designedSides.front.designed = true;
                }

                // Update pricing again after rendering front
                updateSidePricing();
            });

            // Keep reference for switching sides
            a = window.savedDesign.front;
        }

        // Save other sides for later
        if (window.savedDesign.back) b = window.savedDesign.back;
        if (window.savedDesign.left_sleeve) c = window.savedDesign.left_sleeve;
        if (window.savedDesign.right_sleeve) d = window.savedDesign.right_sleeve;
    }



    // $('#sizechange').change(function(){
    // 	var sizeval = $(this).val()
    // 	$('#size_num').text(sizeval)
    // 	var activeObject = canvas.getActiveObject(),
    // 	activeGroup = canvas.getActiveGroup();
    // 	if (activeObject) {
    // 		var min_size = 150;
    // 		var puls_size = min_size + parseInt(sizeval)
    // 		activeObject.scaleToHeight(puls_size)
    // 		activeObject.scaleToWidth(puls_size)


    // 	}
    // 	else if (activeGroup) {
    // 		var objectsInGroup = activeGroup.getObjects();
    // 		canvas.discardActiveGroup();
    // 		objectsInGroup.forEach(function(object) {
    // 			// canvas.remove(object);
    // 			var min_size = 150;
    // 			var puls_size = min_size + parseInt(sizeval)

    // 			object.scaleToHeight(puls_size)
    // 			object.scaleToWidth(puls_size)
    // 		});
    // 	}
    // 	else{
    // 		$(this).val(0)
    // 		$('#size_num').text(0)
    // 	}

    // 	canvas.renderAll();
    // })


    // $('#move_hr').change(function(){
    // 	// console.log('work')
    // 	var hrval = $(this).val()
    // 	$('#move_hr_num').text(hrval)
    // 	var activeObject = canvas.getActiveObject(),
    // 	activeGroup = canvas.getActiveGroup();
    // 	if (activeObject) {
    // 		var min_move = 100;
    // 		var puls_left = min_move + parseInt(hrval)

    // 		activeObject.set({ 
    // 			left: puls_left,
    // 		});

    // 	}
    // 	else if (activeGroup) {
    // 		var objectsInGroup = activeGroup.getObjects();
    // 		canvas.discardActiveGroup();
    // 		objectsInGroup.forEach(function(object) {
    // 			var min_move= 100;
    // 			var puls_left = min_move + parseInt(hrval)
    // 			object.set({ 
    // 				left: puls_left,
    // 			});

    // 		});
    // 	}
    // 	else{
    // 		$(this).val(0)
    // 		$('#move_hr_num').text(0)
    // 	}

    // 	canvas.renderAll();
    // })




    // $('#move_vr').change(function(){
    // 	// console.log('work')
    // 	var vrval = $(this).val()
    // 	$('#move_vr_num').text(vrval)
    // 	var activeObject = canvas.getActiveObject(),
    // 	activeGroup = canvas.getActiveGroup();
    // 	if (activeObject) {
    // 		var min_move = 100;
    // 		var puls_top = min_move + parseInt(vrval)

    // 		activeObject.set({ 
    // 			top: puls_top,
    // 		});

    // 	}
    // 	else if (activeGroup) {
    // 		var objectsInGroup = activeGroup.getObjects();
    // 		canvas.discardActiveGroup();
    // 		objectsInGroup.forEach(function(object) {
    // 			var min_move = 100;
    // 			var puls_top = min_move + parseInt(vrval)
    // 			object.set({ 

    // 				top: puls_top,

    // 			});

    // 		});
    // 	}
    // 	else{
    // 		$(this).val(0)
    // 		$('#move_vr_num').text(0)
    // 	}

    // 	canvas.renderAll();
    // })



    // $('#rotate_slider').change(function(){
    // 	// console.log('work')
    // 	var rotval = $(this).val()

    // 	$('#move_rot_num').text(rotval)

    // 	var activeObject = canvas.getActiveObject(),
    // 	activeGroup = canvas.getActiveGroup();
    // 	if (activeObject) {
    // 		var min_rotate = 0;
    // 		var puls_rotate = min_rotate + parseInt(rotval)

    // 		activeObject.set({ 
    // 			angle: puls_rotate,
    // 		});

    // 	}
    // 	else if (activeGroup) {
    // 		var objectsInGroup = activeGroup.getObjects();
    // 		canvas.discardActiveGroup();
    // 		objectsInGroup.forEach(function(object) {
    // 			var min_rotate = 0;
    // 			var puls_rotate = min_rotate + parseInt(rotval)
    // 			object.set({ 

    // 				angle: puls_rotate,

    // 			});

    // 		});
    // 	}
    // 	else{
    // 		$(this).val(0)
    // 		$('#move_rot_num').text(0)
    // 	}

    // 	canvas.renderAll();
    // })



    // canvas.on({
    // 	 'object:moving': function(e) {		  	
    // 	    e.target.opacity = 0.5;
    // 	  },
    // 	  'object:modified': function(e) {		  	
    // 	    e.target.opacity = 1;

    // 	  },

    // 	 'object:selected':onObjectSelected,
    // 	 'selection:cleared':onSelectedCleared
    //  });

    function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}




/// Step 1: Open the popup when "Add to Bag" is clicked
$(document).on('click', '#CusaddToTheBag', function () {
    if ($("#totalQty").text() == '0') {
        // alert('Please add quantity first');
        showToast('Please add quantity first.', 'error');
        return;
    }
    $("#customDesignPopup_wrapper").fadeIn(200);
});

// Step 2: Cancel button closes popup
$(document).on('click', '#customDesignPopup_cancel', function () {
    $("#customDesignPopup_wrapper").fadeOut(200);
});
if (!document.getElementById('toastContainer')) {
  const container = document.createElement('div');
  container.id = 'toastContainer';
  document.body.appendChild(container);
}

// Reusable function
function showToast(message, type = 'success', duration = 3000) {
  const container = document.getElementById('toastContainer');
  
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;

  container.appendChild(toast);

  // Animate in
  setTimeout(() => {
    toast.classList.add('show');
  }, 10);

  // Remove after duration
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => container.removeChild(toast), 500); // wait for fade out
  }, duration);
}


// --- Render design onto high-res mockup ---
async function renderHighResMockup(side, scale = 4) {
    return new Promise(resolve => {
        const mockupImg = new Image();
        mockupImg.crossOrigin = "anonymous";
        mockupImg.src = $("#shirtDiv img").attr("src");

        mockupImg.onload = () => {
            const width = mockupImg.width * scale;
            const height = mockupImg.height * scale;

            const offCanvas = document.createElement("canvas");
            offCanvas.width = width;
            offCanvas.height = height;
            const ctx = offCanvas.getContext("2d");

            // Draw shirt base
            ctx.drawImage(mockupImg, 0, 0, width, height);

            // Export design-only in HD
            const designHD = canvas.toDataURL({
                format: "png",
                multiplier: scale
            });

            const designImg = new Image();
            designImg.onload = () => {
                // IMPORTANT: Match the exact bounding area of design canvas
                const tcanvas = document.getElementById("tcanvas");
                const rect = tcanvas.getBoundingClientRect();

                const dx = rect.left * scale;
                const dy = rect.top * scale;
                const dw = rect.width * scale;
                const dh = rect.height * scale;

                ctx.drawImage(designImg, dx, dy, dw, dh);

                resolve(offCanvas.toDataURL("image/png"));
            };
            designImg.src = designHD;
        };
    });
}


// --- HD DESIGN ONLY ---
function exportHDDesign(multiplier = 4) {
    return canvas.toDataURL({
        format: "png",
        multiplier: multiplier
    });
}


// --- MAIN CODE ---
$(document).on('click', '#customDesignPopup_confirm', async function () {

    const designName = $("#customDesignPopup_input").val().trim();
    if (!designName) {
        showToast('Please enter a name for your design.', 'error');
        return;
    }

    const btn = $(this);
    btn.prop('disabled', true).text('Saving Design...');

    saveCurrentCanvasState(currentView);

    let attr_id = $("#product_attr").val();
    // Fallback to the template's {% csrf_token %} if the cookie is missing
    const csrftoken = getCookie('csrftoken') || $("[name=csrfmiddlewaretoken]").first().val();

    try {
        // ================= SAVE DESIGN =================
        const designData = {
            email: $("#email_input").val() || "guest@noemail.com",
            tshirtColor: $("#shirtDiv").css('background-color'),
            front: a || "",
            back: b || "",
            left_sleeve: c || "",
            right_sleeve: d || "",
            attr_id: attr_id,
            product_id: $("#mockup_id").val(),
            mockup_id: $("#main_mockup_id").val(),
            name: designName
        };

        const saveRes = await fetch("/save-design/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrftoken
            },
            body: JSON.stringify(designData)
        });

        const saveData = await saveRes.json().catch(() => ({}));
        if (!saveRes.ok || !saveData.success) {
            throw new Error(`Design save failed (HTTP ${saveRes.status}) ${saveData.error || ""}`);
        }

        const uid = saveData.uid;
        btn.text('Capturing Images...');

        // ================= HD CAPTURE =================
        const sides = ["front", "back", "left_sleeve", "right_sleeve"];
        let capturedMockupImages = {};
        let capturedDesignOnlyImages = {};

        const originalView = currentView;

        for (let side of sides) {
            await new Promise(resolve => {
                changeSide(side);
                setTimeout(async () => {
                    canvas.discardActiveObject();
                    canvas.renderAll();

                    capturedDesignOnlyImages[side] = exportHDDesign(4);
                    capturedMockupImages[side] = await domtoimage.toPng(
                        document.getElementById('shirtDiv')
                    );

                    resolve();
                }, 500);
            });
        }

        changeSide(originalView);

        // ================= SIZES =================
        // let sizes = {};
        // $(".size-row").each(function () {
        //     const size = $(this).find(".size-label").text().trim();
        //     const qty = parseInt($(this).find("input").val()) || 0;
        //     if (qty > 0) sizes[size] = qty;
        // });
        
         const sizeData = [];

        document.querySelectorAll("#selectedItems p").forEach(p => {
            const sizeText = p.querySelector(".size-label")?.innerText || 
                            p.childNodes[0].textContent.split("(")[0].trim(); // fallback
            const qty = parseInt(p.childNodes[0].textContent.match(/\((\d+)\)/)[1]);
            const priceEach =
  parseFloat(p.querySelector(".price_each")?.innerText) ||
  parseFloat(p.querySelector(".price_each_one")?.innerText);

            sizeData.push({
                size: sizeText,
                qty: qty,
                priceEach: priceEach
            });
        });

        console.log(sizeData);

        let each_price = $(".price_each").length
            ? parseFloat($(".price_each").text())
            : parseFloat($(".price_each_one").text());

        let estimatedTotal = parseFloat($("#estimatedFinalTotal").text());

        // ================= FORM DATA =================
        const formData = new FormData();

        formData.append("product_id", $("#mockup_id").val());
        formData.append("attr_id", attr_id);
        formData.append("uid", uid);
        formData.append("each_price", each_price);
        formData.append("estimatedTotal", estimatedTotal);
        formData.append("quantities", JSON.stringify(sizeData));

        formData.append("canvas_json", JSON.stringify({
            front: a,
            back: b,
            left_sleeve: c,
            right_sleeve: d
        }));

        formData.append("mockup_images", JSON.stringify(capturedMockupImages));
        formData.append("design_only_images", JSON.stringify(capturedDesignOnlyImages));

        // ================= UPLOADED FILES =================
        Object.keys(window.uploadedDesignFiles).forEach(side => {
            window.uploadedDesignFiles[side].forEach(item => {

                formData.append(
                    "uploaded_files",
                    item.file,
                    item.filename
                );

                formData.append(
                    "uploaded_files_meta",
                    JSON.stringify({
                        filename: item.filename,
                        side: item.side
                    })
                );
            });
        });

        btn.text('Adding to cart...');

        const cartRes = await fetch("/add-to-cart/", {
            method: "POST",
            headers: {
                "X-CSRFToken": csrftoken
            },
            body: formData
        });

        if (!cartRes.ok) {
            const cartData = await cartRes.json().catch(() => ({}));
            throw new Error(`Add to cart failed (HTTP ${cartRes.status}) ${cartData.error || ""}`);
        }

        window.location.href = "/cart/";

    } catch (err) {
        console.error(err);
        alert("Something went wrong. Please try again.");
    } finally {
        btn.prop('disabled', false).text('Add to Cart');
        $("#customDesignPopup_wrapper").fadeOut(200);
    }
});

    // $("#CusaddToTheBag").click(function () {
    //     $('#drawingArea').css({ 'outline': 'none' })
    //     $('#shirtDiv').css({ 'outline': 'none' })
    //     $('#flip').css({ 'display': 'none' })
    //     var node = document.getElementById('shirtDiv');

    //     domtoimage.toPng(node)
    //         .then(function (dataUrl) {
    //             var img = document.getElementById('front_mockup_img_preview')
    //             img.value = dataUrl;
                
    //             var get_select_desgin_front = $('#fornt_design_id').val()
    //             var get_select_desgin_back = $('#back_design_id').val()

    //             var get_select_text_front = $('#text_print_front').val()
    //             var get_select_text_back = $('#text_print_back').val()
    //             $('#Main_cus_form_id').submit()

    //             // if(get_select_desgin_front || get_select_desgin_back  || get_select_text_front || get_select_text_back){
    //             // 	$('#Main_cus_form_id').submit()

    //             // }else{
    //             // 	$('.add_to_cart_error').text("Please Select Design Before Add To Cart")
    //             // 	$('.add_to_cart_error').show()
    //             // }
    //             // $('#drawingArea').css({'outline':'2px dashed #cccccc'})
    //             // $('#shirtDiv').css({'outline':'2px dashed #000000'})
    //             // $('#flip').css({'display':'block'})
    //             // document.body.appendChild(img);
    //         })
    //         .catch(function (error) {
    //             console.error('oops, something went wrong!', error);

    //             // $('#drawingArea').css({'outline':'2px dashed #cccccc'})
    //             // $('#shirtDiv').css({'outline':'2px dashed #000000'})
    //             // $('#flip').css({'display':'block'})

    //             $('#Main_cus_form_id').submit()

    //             // var get_select_desgin_front = $('#fornt_design_id').val()
    //             // if(get_select_desgin_front){
    //             // 	$('#Main_cus_form_id').submit()

    //             // }else{
    //             // 	$('.add_to_cart_error').text("Please Select Design Before Add To Cart" )
    //             // 	$('.add_to_cart_error').show()
    //             // }
    //         });

    // })



    // piggyback on `canvas.findTarget`, to fire "object:over" and "object:out" events
    canvas.findTarget = (function (originalFn) {
        return function () {
            var target = originalFn.apply(this, arguments);
            if (target) {
                if (this._hoveredTarget !== target) {
                    canvas.fire('object:over', { target: target });
                    if (this._hoveredTarget) {
                        canvas.fire('object:out', { target: this._hoveredTarget });
                    }
                    this._hoveredTarget = target;
                }
            }
            else if (this._hoveredTarget) {
                canvas.fire('object:out', { target: this._hoveredTarget });
                this._hoveredTarget = null;
            }
            return target;
        };
    })(canvas.findTarget);

    canvas.on('object:over', function (e) {
        //   e.target.setFill('red');
        //   canvas.renderAll();

    });

    canvas.on('object:out', function (e) {
        //   e.target.setFill('green');
        //   canvas.renderAll();
    });

    // document.getElementById('add-text').onclick = function() {
    // 	var json = canvas.toJSON();
    // 	canvas.clear();
    // 	appar_close()
    // 	var text = $("#text-string").val();

    //     var textSample = new fabric.Text(text, {
    //       left: 100,
    //       top: 100,
    //       fontFamily: 'helvetica',
    //       angle: 0,
    //       fill: '#000000',
    //       scaleX: 0.5,
    //       scaleY: 0.5,
    //       fontWeight: '',
    // 	  hasRotatingPoint:true
    //     });	

    // 	var text_price = $("#text_price").val()

    //     canvas.add(textSample);	
    //     canvas.item(canvas.item.length-1).hasRotatingPoint = true;    
    //     $("#texteditor").css('display', 'block');
    //     $("#imageeditor").css('display', 'block');
    // 	$('.opt_range').val(0)


    // 	if ($('#mock_flip').val() == "Show Back View") {
    // 		$('#text_print_front').val(text)
    // 		$('#text_print_front_price').val(text_price)
    // 		$('.dynamic_price_text_fornt').text(text_price)
    // 		total_calc()


    // 	}else{
    // 		$('#text_print_back').val(text)
    // 		$('#text_print_back_price').val(text_price)
    // 		$('.dynamic_price_text_back').text(text_price)
    // 		total_calc()
    // 	}




    // };
    // $("#text-string").keyup(function(){	  		
    // 	var activeObject = canvas.getActiveObject();
    //       if (activeObject && activeObject.type === 'text') {
    //     	  activeObject.text = this.value;
    //     	  canvas.renderAll();
    //       }
    // });

    function addDeleteControl(obj) {
    obj.setControlsVisibility({
        mt: true, mb: true, ml: true, mr: true,
        bl: true, br: true, tl: true, tr: true, mtr: true
    });

    obj.controls.deleteControl = new fabric.Control({
        x: 0.4,
        y: -0.4,
        offsetX: -6,
        offsetY: -6,
        cursorStyle: 'pointer',

        mouseUpHandler: function (eventData, transform) {
            let target = transform.target;
            let sideKey = target.sideKey;

            /* ===============================
               1️⃣ REMOVE FROM MEMORY (IMAGES)
            =============================== */
            if (
                target.customData &&
                target.customData.filename &&
                sideKey &&
                window.uploadedDesignFiles &&
                window.uploadedDesignFiles[sideKey]
            ) {
                window.uploadedDesignFiles[sideKey] =
                    window.uploadedDesignFiles[sideKey].filter(
                        item => item.filename !== target.customData.filename
                    );
            }

            /* ===============================
               2️⃣ REMOVE FROM CANVAS
            =============================== */
            canvas.remove(target);
            canvas.requestRenderAll();

            /* ===============================
               3️⃣ UPDATE SIDE DESIGN STATE
            =============================== */
            console.log('side', sideKey, designedSides, designedSides[sideKey]);
            if (sideKey && designedSides[sideKey]) {
                
                let stillDesigned = canvas
                    .getObjects()
                    .some(obj => obj.sideKey === sideKey);

                designedSides[sideKey].designed = stillDesigned;

                // optional: reset embroidery if nothing left
                if (!stillDesigned) {
                    designedSides[sideKey].embroidery = false;
                }
            }

            /* ===============================
               4️⃣ UPDATE PRICING
            =============================== */
            updateSidePricing();

            return true;
        },

        render: function (ctx, left, top) {
            let size = 25;
            let img = document.createElement('img');
            img.src = '/static/shop/img/delete.png';
            ctx.drawImage(img, left - size / 2, top - size / 2, size, size);
        },

        cornerSize: 16
    });

    obj.cornerStyle = 'circle';
    obj.cornerColor = 'rgba(0,0,0,0.5)';
    canvas.renderAll();
}

    const uploadBox = document.getElementById("uploadBox");
    const fileInput = document.getElementById("uploadSticker");

    // Click → open file dialog
    uploadBox.addEventListener("click", () => fileInput.click());

    // Drag events
    uploadBox.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadBox.classList.add("dragover");
    });
    uploadBox.addEventListener("dragleave", () => {
        uploadBox.classList.remove("dragover");
    });
    uploadBox.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadBox.classList.remove("dragover");
        fileInput.files = e.dataTransfer.files;

        // trigger change event manually (so your existing code runs)
        const event = new Event("change");
        fileInput.dispatchEvent(event);
    });




    function addLayerToList(obj, type) {
        let id = "layer_" + (++layerIdCounter);
        obj.layerId = id; // link canvas object with list item

        let editButton = (type === "textbox") ? `
        <button class="layer-edit">
          <i class="fa-solid fa-pen"></i>
        </button>` : "";

        let html = `
      <li id="${id}">
	  <span class="layer-handle"><i class="fa-solid fa-up-down-left-right"></i></span>
        <div class="layer-thumb">
          ${type === "textbox" ?
                `<span class="layer-thumb-text">"${obj.text}"</span>` :
                `<img src="${obj.getSrc()}" class="layer-img" width="40">`
            }
        </div>
        ${editButton}
        <button class="layer-delete">
          <i class="fa-solid fa-trash"></i>
        </button>
      </li>
    `;
        $("#layersList").prepend(html);

        // edit handler (only if text)
        if (type === "textbox") {
            $("#" + id + " .layer-edit").click(function () {
                canvas.setActiveObject(obj);
                $("#mainMenu").hide();
                $("#textPanel").show();
                $("#editTextOptions").show();
                updateControls(obj);
                appar_open();
            });
        }

        // delete handler
        $("#" + id + " .layer-delete").click(function () {
            // Remove from canvas
            canvas.remove(obj);
            $("#" + id).remove();

            // --- Deduct price from cart (same as delete control) ---
            const design_id = obj.design_id || obj.custom_id;
            const price = obj.price || 0;

            let sideKey = "";
            if (currentView === "front") sideKey = "front";
            else if (currentView === "back") sideKey = "back";
            else if (currentView === "left_sleeve") sideKey = "left_sleeve";
            else if (currentView === "right_sleeve") sideKey = "right_sleeve";

            designedSides[sideKey].designed = false;

            updateSidePricing()

            // if ($('#mock_flip').val() == "Show Back View") {
            //     // Clear front design
            //     $("#fornt_design_id").val('');
            //     $("#fornt_design_price").val(0);
            //     $('.dynamic_price_fornt').text('0');
            // } else {
            //     // Clear back design
            //     $("#back_design_id").val('');
            //     $("#back_design_price").val(0);
            //     $('.dynamic_price_back').text('0');
            // }

            // total_calc();
            // Recalculate total

            canvas.requestRenderAll();
        });
    }

    new Sortable(document.getElementById('layersList'), {
        handle: ".layer-handle",
        animation: 150,
        onEnd: function (evt) {
            reorderCanvasLayers();
        }
    });

    function reorderCanvasLayers() {
        let order = $("#layersList li").map(function () {
            return this.id;
        }).get();

        // Loop and reorder canvas objects
        order.reverse().forEach((layerId, index) => {
            let obj = canvas.getObjects().find(o => o.layerId === layerId);
            if (obj) {
                canvas.bringToFront(obj); // ensures top stacking
            }
        });

        canvas.renderAll();
    }


    $(document).ready(function () {
        let currentStep = 1;
        let uploadedFile = null;
        let completedSteps = [];

        // Open modal
        $('#uploadTrigger').click(function () {
            $('#uploadModal').fadeIn(300);
            $('body').css('overflow', 'hidden');
        });

        // Close modal
        $('#closeModal').click(function () {
            closeModal('#uploadModal');
        });

        $('.upload-modal-overlay').click(function (e) {
            if (e.target === this) {
                closeModal('#uploadModal');
            }
        });

        function closeModal(e) {
            $(e).fadeOut(300);
            $('body').css('overflow', 'auto');
        }

        function rgbToHex(rgb) {
    const match = rgb.match(/\d+/g);
    if (!match) return rgb;
    return (
        "#" +
        match
            .slice(0, 3)
            .map(x => {
                const hex = parseInt(x).toString(16);
                return hex.length === 1 ? "0" + hex : hex;
            })
            .join("")
            .toUpperCase()
    );
}


        $(document).ready(function () {

    function loadSizesForColor(colorCode, productId, colorId, attributeId) {
        if (!colorId || !productId) return;

        // Apply color background
        $("#shirtDiv").css('background-color', colorCode);
        $(".preview-images .canvas-container, .dp-popup-content").css('background-color', colorCode);

        // Update hidden input for backend form submission
        $("#product_attr").val(attributeId);

        // Fetch sizes by color ID
        $.ajax({
            url: `/get-sizes/${productId}/?attr_id=${attributeId}&color_id=${encodeURIComponent(colorId)}`,
            method: 'GET',
            success: function (response) {
                const box = $(".size-qty-box");
                box.empty();
                

                if (response.sizes && response.sizes.length > 0) {
                    response.sizes.forEach(size => {
                        box.append(`
                            <div class="size-row" data-price='${size.price}'>
                                <div class="size-row-body">
                                    <span class="size-label">${size.size}</span>
                                    <div class="qty-control">
                                        <button class="qty-btn minus">−</button>
                                        <input type="number" value="0" max="${size.max_qty}" >
                                        <button class="qty-btn plus">+</button>
                                    </div>
                                </div>
                                <small class="error-text" style="color:red; display:none;">
                                    You can’t order more than ${size.max_qty}. Contact sales.
                                </small>
                            </div>
                        `);
                    });

                    box.append(`
                        <button type="button" class="btn btn-large btn-block btn-success button_class">
                            Get Price <i class="icon-briefcase icon-white"></i>
                        </button>
                    `);

                    $("#product_attr").val(response.attr_id);

                    bindPopupHandler(); // Reattach popup handler
                } else {
                    box.append(`<p class="no-sizes">No sizes available for this color.</p>`);
                }
            },
            error: function (xhr) {
                console.error('Error fetching sizes:', xhr);
            }
        });
    }

    // 🧩 Popup logic separated into a reusable function
    function bindPopupHandler() {
        const popup = document.getElementById("pricePopup");
        const closeBtn = document.querySelector(".popup-close");

        $(".button_class").off("click").on("click", function () {
            let itemsDiv = $("#selectedItems").empty();
            let totalQty = 0;
            let priceEach = parseFloat($(".dynamic_price_total").text()) || 0;

            $(".size-row").each(function () {
                let size = $(this).find(".size-label").text();
                let qty = parseInt($(this).find("input").val()) || 0;
                if (qty > 0) {
                    itemsDiv.append(`<p>${size} (${qty}) x $${priceEach.toFixed(2)} each</p>`);
                    totalQty += qty;
                }
            });

            $("#totalQty").text(totalQty);
            $("#estimatedTotal").text((totalQty * priceEach).toFixed(2));

            popup.style.display = "flex";
        });

        $(closeBtn).off("click").on("click", () => popup.style.display = "none");
        $(window).off("click").on("click", e => {
            if (e.target === popup) popup.style.display = "none";
        });
    }

    // 🟢 Load saved color on page load
    const savedColorCode = $("#shirtDiv").data("color-code");
    const savedColorId = $("#shirtDiv").data("color-id");
    const productId = $("#mockup_id").val();
    const attributeId = $("#product_attr").val();

    if (savedColorId && savedColorCode) {
        loadSizesForColor(savedColorCode, productId, savedColorId, attributeId);
    }

    // 🎨 When clicking color swap
    $(".tshirt-swap-btn").click(function () {
        const activeSwatch = $(".tshirt-color-swatch.active");
        const colorCode = activeSwatch.css("background-color");
        const hexColor = rgbToHex(colorCode);
        const colorId = activeSwatch.data("color-id");
        const attr_Id = activeSwatch.data("attr-id");
        const dis_price = parseFloat(activeSwatch.data("dis-price")) || 0;
        $(".dynamic_price_total").text(dis_price.toFixed(2))
        baseProductPrice = dis_price

        

        loadSizesForColor(hexColor, productId, colorId, attr_Id);
        closeModal("#productModal");
    });

    // ✅ Helper to convert rgb() → hex
    function rgbToHex(rgb) {
        const match = rgb.match(/\d+/g);
        if (!match) return rgb;
        return "#" + match.map(x => {
            const hex = parseInt(x).toString(16);
            return hex.length === 1 ? "0" + hex : hex;
        }).join("");
    }
});

        $('.upload-step-tab').click(function () {
            const step = parseInt($(this).data('step'));
            if (completedSteps.includes(step) || step <= currentStep) {
                showStep(step);
            }
        });

        $('#nextBtn').click(function () {
            if (currentStep < 3) {
                if (validateCurrentStep()) {
                    if (!completedSteps.includes(currentStep)) {
                        completedSteps.push(currentStep);
                    }
                    showStep(currentStep + 1);
                }
            } else {
                // Final submit
                submitForm();
            }
        });

        $('#prevBtn').click(function () {
            if (currentStep > 1) {
                showStep(currentStep - 1);
            }
        });

        $('#productTrigger').click(function () {
            $('#productModal').fadeIn(300);
            $('body').css('overflow', 'hidden');
        });

        // Close modal
        $('#productCloseModal').click(function () {
            closeModal('#productModal');
        });

        $('.product-upload-modal-overlay').click(function (e) {
            if (e.target === this) {
                closeModal('#productModal');
            }
        });

        function validateCurrentStep() {
            switch (currentStep) {
                case 1:
                    if (!uploadedFile) {
                        showNotification('Please upload a file first.', 'warning');
                        return false;
                    }
                    if (!$('#termsCheck').is(':checked')) {
                        showNotification('Please agree to the terms and conditions.', 'warning');
                        return false;
                    }
                    return true;
                case 2:
                    if (!$('.upload-process-btn.selected').length) {
                        showNotification('Please select a production process.', 'warning');
                        return false;
                    }
                    return true;
                case 3:
                    return true;
                default:
                    return true;
            }
        }

        function showNotification(message, type = 'info') {
            const notification = $(`
                    <div class="upload-notification ${type}" style="
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        background: ${type === 'warning' ? '#fbbf24' : '#3b82f6'};
                        color: white;
                        padding: 15px 20px;
                        border-radius: 8px;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                        z-index: 10001;
                        animation: slideInRight 0.3s ease-out;
                    ">
                        ${message}
                    </div>
                `);

            $('body').append(notification);
            setTimeout(() => {
                notification.fadeOut(300, () => notification.remove());
            }, 3000);
        }

        fabric.Object.prototype.stateProperties = fabric.Object.prototype.stateProperties.concat(['sideKey']);



        document.getElementById("saveDesignBtn").addEventListener("click", function () {
    $("#saveDesignBtn").text('Saving...');

    let email = document.getElementById("designEmail").value.trim();
    let emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!email || !emailPattern.test(email)) {
        showNotification('Please enter a valid email!', 'warning');
        $("#saveDesignBtn").text('Save Design');
        return;
    }

    // Save the current view before sending data
    saveCurrentCanvasState(currentView);

    let tshirtColor = $("#shirtDiv").css('background-color');
    let attr_id = $("#product_attr").val();

    // Build design data for all views
    let designData = {
        email: email,
        tshirtColor: tshirtColor,
        attr_id: attr_id,
        front: a || "",
        back: b || "",
        left_sleeve: c || "",
        right_sleeve: d || "",
        product_id: document.getElementById("mockup_id").value,
        mockup_id: document.getElementById("main_mockup_id").value
    };

    fetch("/save-design/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify(designData)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showNotification('Design saved! A link has been sent to your email!', 'success');
            $("#saveDesignBtn").text('Save Design');
            $("#designEmail").val('');
        } else {
            showNotification('Something went wrong while saving!', 'error');
            $("#saveDesignBtn").text('Save Design');
        }
    })
    .catch(err => {
        console.error("Error saving design:", err);
        showNotification('Error occurred while saving. Please try again.', 'error');
        $("#saveDesignBtn").text('Save Design');
    });
});


        // CSRF helper (Django)
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== "") {
                let cookies = document.cookie.split(";");
                for (let i = 0; i < cookies.length; i++) {
                    let cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + "=")) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }



        // File input handling
        $('#chooseFileBtn').click(function () {
            $('#fileInput').click();
        });
        $('#dropZone    ').click(function () {
            $('#fileInput').click();
        });

        $('#fileInput').change(function () {
            const file = this.files[0];
            if (file) {
                handleFileUpload(file);
            }
        });

        // Drag and drop
        $('#dropZone').on('dragover', function (e) {
            e.preventDefault();
            $(this).addClass('dragover');
        });

        $('#dropZone').on('dragleave', function (e) {
            e.preventDefault();
            $(this).removeClass('dragover');
        });

        $('#dropZone').on('drop', function (e) {
            e.preventDefault();
            $(this).removeClass('dragover');

            const files = e.originalEvent.dataTransfer.files;
            if (files.length > 0) {
                handleFileUpload(files[0]);
            }
        });

        $('.upload-process-btn').click(function () {
            // remove active class from all
            $('.upload-process-btn').removeClass('selected');
            // hide all messages
            $('.upload-process-btn .process-msg').hide();

            // add active class to clicked one
            $(this).addClass('selected');
            // show its message
            $(this).find('.process-msg').show();
        });

        function showStep(step) {
            currentStep = step;

            // Update tabs
            $('.upload-step-tab').removeClass('active-step');
            $(`.upload-step-tab[data-step="${step}"]`).addClass('active-step');

            // Mark completed steps
            $('.upload-step-tab').removeClass('completed-step');
            completedSteps.forEach(completedStep => {
                if (completedStep < step) {
                    $(`.upload-step-tab[data-step="${completedStep}"]`).addClass('completed-step');
                }
            });

            // Update content
            $('.upload-step-content').removeClass('active-content');
            $(`#step${step}`).addClass('active-content');

            // Update navigation buttons
            $('#prevBtn').prop('disabled', step === 1);
            $('#currentStepNum').text(step);

            if (step === 3) {
                $('#nextBtn').html('<i class="fa fa-check"></i> Complete Upload');
            } else {
                $('#nextBtn').html('Next <i class="fa fa-arrow-right"></i>');
            }
        }

        function submitForm() {
    if (!uploadedFile) {
        showNotification('No file to upload!', 'warning');
        return;
    }

    if (typeof canvas === 'undefined' || !canvas) {
        showNotification('Canvas not found!', 'warning');
        return;
    }

    // ===== SIDE =====
    let sideKey = currentView; // front | back | left_sleeve | right_sleeve
    if (!window.uploadedDesignFiles[sideKey]) {
        showNotification('Invalid design side!', 'error');
        return;
    }

    // ===== GENERATE FILE NAME =====
    const ext = uploadedFile.name.split('.').pop();
    const uniqueId = Math.floor(100 + Math.random() * 9000); // 3–4 digits
    let add_inst = $('.upload-notes-textarea').val();
    console.log('add', add_inst);
    
    let generatedFilename;

    if (add_inst != '') {
        generatedFilename = `${add_inst}.${ext}`;
    } else {
        generatedFilename = `no_additional_instructions_${uniqueId}.${ext}`;
    }
    console.log('generatedFilename', generatedFilename);
    

    // ===== STORE FILE IN MEMORY =====
    window.uploadedDesignFiles[sideKey].push({
        file: uploadedFile,
        filename: generatedFilename,
        side: sideKey
    });


    // ===== LOAD IMAGE INTO FABRIC =====
    let reader = new FileReader();
    reader.onload = function (f) {
        fabric.Image.fromURL(f.target.result, function (image) {

            image.set({
                left: 0,
                top: 100,
                angle: 0,
                padding: 10,
                cornerSize: 15,
                hasRotatingPoint: true,
                selectable: true
            });

            image.scaleToWidth(100);
            image.scaleToHeight(100);

            image.sideKey = sideKey;

            // 🔑 Attach metadata
            image.customData = {
                source: "user_upload",
                side: sideKey,
                filename: generatedFilename
            };

            canvas.add(image);

            if (typeof addDeleteControl === 'function') {
                addDeleteControl(image);
            }

            canvas.setActiveObject(image);
            canvas.centerObject(image);
            canvas.renderAll();

            addLayerToList(image, 'image');

            // ===== MARK SIDE DESIGNED =====
            designedSides[sideKey].designed = true;

            if ($(".upload-process-btn.selected").attr('data-process') === 'embroidery') {
                designedSides[sideKey].embroidery = true;
            }

            updateSidePricing();

            $('.opt_range').val(0);

            showNotification('Image added to canvas successfully!', 'success');

            setTimeout(() => {
                closeModal('#uploadModal');
                resetModal();
            }, 1200);
        });
    };

    reader.readAsDataURL(uploadedFile);
}


        function resetModal() {
            currentStep = 1;
            uploadedFile = null;
            completedSteps = [];
            showStep(1);
            $('#dropZone').html(`
                    <div class="upload-preview-placeholder">
                        <i class="fa fa-image"></i>
                    </div>
                    <div style="color: #6b7280; font-size: 16px; font-weight: 500; margin-top: 10px;">Drop your image here</div>
                    <div style="color: #9ca3af; font-size: 14px; margin-top: 5px;">or click to browse</div>
                `);
            $('#fileInput').val('');
            $('#termsCheck').prop('checked', false);
            $('.upload-notes-textarea').val('');
            $('.upload-process-btn').removeClass('selected');
            $('.upload-process-btn').first().addClass('selected');
        }

        function handleFileUpload(file) {
            // Validate file type
            const allowedTypes = ['image/jpeg', 'image/jpg', 'image/gif', 'image/png', 'image/webp', 'image/bmp', 'image/tiff', 'application/postscript', 'image/svg+xml', 'application/pdf'];
            const allowedExtensions = ['.jpg', '.jpeg', '.gif', '.png', '.webp', '.bmp', '.tif', '.tiff', '.ai', '.eps', '.svg', '.pdf', '.psd'];

            const fileName = file.name.toLowerCase();
            const isValidType = allowedTypes.includes(file.type) || allowedExtensions.some(ext => fileName.endsWith(ext));

            if (!isValidType) {
                showNotification('Please upload a valid image file (JPG, GIF, PNG, WEBP, BMP, TIF, AI, EPS, SVG, PDF, PSD)', 'warning');
                return;
            }

            // Validate file size (10MB = 10 * 1024 * 1024 bytes)
            const maxSize = 25 * 1024 * 1024;
            if (file.size > maxSize) {
                uploadedFile = null; 
                showNotification('File size must be less than 25MB', 'warning');
                return;
            }

            // Store the uploaded file
            uploadedFile = file;

            // Create preview for image files
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    const imageUrl = e.target.result;

                    // Update drop zone with preview
                    $('#dropZone').html(`
                            <div style="display: flex; flex-direction: column; align-items: center;">
                                <img src="${imageUrl}" alt="Preview" style="max-width: 120px; max-height: 120px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                                <div style="color: #059669; font-weight: 600; font-size: 16px;">✓ ${file.name}</div>
                                <div style="color: #6b7280; font-size: 14px; margin-top: 5px;">${(file.size / 1024 / 1024).toFixed(2)} MB</div>
                            </div>
                        `);

                    // Update step 2 and 3 images
                    $('#step2Image, #step3Image').attr('src', imageUrl);
                };
                reader.readAsDataURL(file);
            } else {
                // For non-image files (PDF, AI, etc.)
                $('#dropZone').html(`
                        <div style="display: flex; flex-direction: column; align-items: center;">
                            <div class="upload-preview-placeholder" style="background: linear-gradient(135deg, #059669, #047857);">
                                <i class="fa fa-file" style="color: white; font-size: 35px;"></i>
                            </div>
                            <div style="color: #059669; font-weight: 600; font-size: 16px; margin-top: 15px;">✓ ${file.name}</div>
                            <div style="color: #6b7280; font-size: 14px; margin-top: 5px;">${(file.size / 1024 / 1024).toFixed(2)} MB</div>
                        </div>
                    `);
            }

            showNotification('File uploaded successfully!', 'success');
        }

        $('<style>').text(`
                @keyframes slideInRight {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `).appendTo('head');
    });

    


    document.querySelectorAll(".single_tab_btn").forEach(btn => {
        btn.addEventListener("click", function () {
            // Remove active class from all buttons
            document.querySelectorAll(".single_tab_btn").forEach(b => b.classList.remove("active"));
            this.classList.add("active");

            // Hide all tab panes
            document.querySelectorAll(".left-tab-pane").forEach(tab => tab.style.display = "none");

            // Show selected tab
            let selectedTab = this.getAttribute("data-tab");
            document.getElementById("tab-" + selectedTab).style.display = "block";
        });
    });

function saveCurrentState() {
    const current = currentView;
    const json = JSON.stringify(canvas);

    if (current === "front") a = json;
    else if (current === "back") b = json;
}

function getDesignImage(side = "front", multiplier = 2) {
    return new Promise((resolve) => {
        // Prefer saved JSON (a/b)
        const json = (side === "front") ? (typeof a !== "undefined" ? a : null)
                                       : (typeof b !== "undefined" ? b : null);

        // If no saved JSON, try using current live canvas (only sensible for front)
        if (!json) {
            if (side === "front" && typeof canvas !== "undefined" && canvas && canvas.getObjects().length) {
                try {
                    const data = canvas.toDataURL({ format: 'png', multiplier });
                    return resolve(data);
                } catch (err) {
                    return resolve(null);
                }
            }
            return resolve(null);
        }

        // Create a temporary static canvas and load JSON, then export DataURL
        const tempWidth = (typeof canvas !== "undefined" && canvas.getWidth) ? canvas.getWidth() : 800;
        const tempHeight = (typeof canvas !== "undefined" && canvas.getHeight) ? canvas.getHeight() : 800;
        const temp = new fabric.StaticCanvas(null, { width: tempWidth, height: tempHeight });

        temp.loadFromJSON(json, function () {
            // ensure rendering completed before export
            temp.renderAll();
            try {
                const data = temp.toDataURL({ format: 'png', multiplier });
                resolve(data);
            } catch (err) {
                resolve(null);
            }
        }, function (o, object) {
            // optional progress callback - ignored
        });
    });
}

// --- Render a small preview into the small canvases ---
function renderPreview(mockupId, mockupImagePath, side = "front") {
    // Create a Fabric canvas for the small preview
    let previewCanvas = new fabric.Canvas(mockupId, { selection: false });

    // disable interactions
    previewCanvas.skipTargetFind = true;
    previewCanvas.interactive = false;
    previewCanvas.forEachObject(obj => obj.selectable = false);

    // Save mockup path and side in dataset so click knows which side to open
    let canvasEl = document.getElementById(mockupId);
    canvasEl.dataset.mockupPath = mockupImagePath;
    canvasEl.dataset.side = side;

    // Load background mockup
    fabric.Image.fromURL(mockupImagePath, function (bgImg) {
        // use canvas width properly
        const w = previewCanvas.getWidth ? previewCanvas.getWidth() : previewCanvas.width;
        bgImg.scaleToWidth(w);
        previewCanvas.setBackgroundImage(bgImg, previewCanvas.renderAll.bind(previewCanvas));

        // Then overlay the design for the requested side (if any)
        getDesignImage(side, 1).then(function (designData) {
            if (designData) {
                fabric.Image.fromURL(designData, function (designImg) {

                    const MAIN_CANVAS_WIDTH = canvas.getWidth();
                    // tweak scale/position so it fits small preview
                    const previewW = previewCanvas.getWidth();
                    const scaleRatio = previewW / MAIN_CANVAS_WIDTH;

                    // match scale
                    designImg.scaleX *= scaleRatio;
                    designImg.scaleY *= scaleRatio;

                    // match position
                    designImg.left *= scaleRatio;
                    designImg.top *= scaleRatio;

                    designImg.selectable = false;
                    designImg.evented = false;

                    designImg.selectable = false;
                    designImg.evented = false;

                    previewCanvas.add(designImg);
                    previewCanvas.renderAll();
                });
            } else {
                // no design for this side -> just render background (empty shirt)
                previewCanvas.renderAll();
            }
        });
    });

    // Match shirt background color for container (keeps your old behavior)
    let color = $("#shirtDiv").css('background-color');
    $('.preview-images .canvas-container').css('background-color', color);
}

// --- Render big popup image for a given mockup path and side (preserves your popup behavior) ---
function renderPopupImage(mockupPath, side = "front") {
    let bigCanvas = new fabric.StaticCanvas(null, { width: 500, height: 600 });

    const MAIN_CANVAS_WIDTH = canvas.getWidth();

    fabric.Image.fromURL(mockupPath, function (bgImg) {
        const w = bigCanvas.getWidth ? bigCanvas.getWidth() : 500;
        bgImg.scaleToWidth(w);
        bigCanvas.setBackgroundImage(bgImg, bigCanvas.renderAll.bind(bigCanvas));

        // Add design in higher res if exists
        getDesignImage(side, 4).then(function (designData) {
            if (designData) {
                fabric.Image.fromURL(designData, function (designImg) {
                    designImg.scaleToWidth(500);
                    designImg.top = 0;
                    designImg.left = 0;
                    designImg.selectable = false;

                    bigCanvas.add(designImg);
                    bigCanvas.renderAll();

                    // Show in popup — same DOM updates as your original code
                    document.getElementById("dp-popup-img").src = bigCanvas.toDataURL("image/png");
                    document.getElementById("dp-popup-img").style.backgroundColor = $("#shirtDiv").css('background-color');
                    document.getElementById("designPreviewPopup").style.display = "block";
                });
            } else {
                // no design → show just the mockup (empty shirt)
                bigCanvas.renderAll();
                document.getElementById("dp-popup-img").src = bigCanvas.toDataURL("image/png");
                document.getElementById("dp-popup-img").style.backgroundColor = $("#shirtDiv").css('background-color');
                document.getElementById("designPreviewPopup").style.display = "block";
            }
        });
    });
}

// --- Build previews when Preview tab is clicked ---
document.querySelector('[data-tab="preview"]').addEventListener("click", function () {
    saveCurrentState();

    const previewCanvases = document.querySelectorAll(".preview-images canvas");

    previewCanvases.forEach((canvasEl) => {
        const path = canvasEl.dataset.url;
        const side = canvasEl.dataset.view;

        if (!path || !side) return;
        renderPreview(canvasEl.id, path, side);
    });
});


// --- Click handler for previews → open popup with correct side ---
document.querySelector(".preview-images").addEventListener("click", function (e) {
    if (e.target.tagName.toLowerCase() === "canvas") {
        const mockupPath = e.target.dataset.url;
        const side = e.target.dataset.view || "front";
        renderPopupImage(mockupPath, side);
    }
});

// --- Keep your popup close handlers as they were ---
document.querySelector(".dp-popup-close").addEventListener("click", function () {
    document.getElementById("designPreviewPopup").style.display = "none";
});

document.getElementById("designPreviewPopup").addEventListener("click", function (e) {
    if (e.target.id === "designPreviewPopup") {
        this.style.display = "none";
    }
});


function updateSidePricing() {
    let total = baseProductPrice;

    for (let side in designedSides) {
        if (designedSides[side].designed) total += designPrices[side];
        if (designedSides[side].embroidery) total += designPrices.embroidery_extra;
    }

    // ✅ expose design cost PER ITEM globally
    window.designCostPerItem = Math.max(0, total - baseProductPrice);

    $(".dynamic_price_total").text(total.toFixed(2));
    $("#estimatedTotal").text(total.toFixed(2));
}



$(".text_panel_open_btn").click(function () {
                document.getElementById('textInputBox').style.display = 'none';
                $("#customText").val("")
                document.getElementById('editTextOptions').style.display = 'block';
            })
            



		document.getElementById('uploadSticker').addEventListener('change', function (e) {
                let file = e.target.files[0];
                if (!file) return;

                let reader = new FileReader();
                reader.onload = function (f) {
                    fabric.Image.fromURL(f.target.result, function (image) {
                        image.set({
                            left: 0,
                            top: 60,
                            angle: 0,
                            padding: 10,
                            cornerSize: 15,
                            hasRotatingPoint: true,
                            selectable: true
                        });
                        image.scaleToHeight(200);
                        image.scaleToWidth(200);

                        canvas.add(image);
                        addDeleteControl(image);
                        canvas.setActiveObject(image);
                        canvas.renderAll();

                        addLayerToList(image, "image");  // 👈 here

                        // === Cart Integration for Image ===
                        const uploadPrice = 5.00; // fixed price for uploaded images
                        const design_id = "custom_upload";

                        $('.add_to_cart_error').hide();

                        if ($('#mock_flip').val() == "Show Back View") {
                            $("#fornt_design_id").val(design_id);

                            let currentPrice = parseFloat($("#fornt_design_price").val()) || 0;
                            let newPrice = currentPrice + uploadPrice;

                            $("#fornt_design_price").val(newPrice);
                            $('.dynamic_price_fornt').text(newPrice.toFixed(2));
                            total_calc();
                        } else {
                            $("#back_design_id").val(design_id);

                            let currentPrice = parseFloat($("#back_design_price").val()) || 0;
                            let newPrice = currentPrice + uploadPrice;

                            $("#back_design_price").val(newPrice);
                            $('.dynamic_price_back').text(newPrice.toFixed(2));
                            total_calc();
                        }

                        $('.opt_range').val(0);
                    });
                };
                reader.readAsDataURL(file);
            });

            canvas.on('object:removed', function (e) {
                if (e.target && e.target.layerId) {
                    $("#" + e.target.layerId).remove();
                }
            });

            /* ===== Sync UI controls with selected text ===== */
            function updateControls(obj) {
            if(!obj) return;

            document.getElementById('editTextArea').value = obj.text || "";
            document.getElementById('fontFamilySelect').value = obj.fontFamily || "Arial";
            document.getElementById('fontColorPicker').value = obj.fill || "#000000";
            document.getElementById('letterSpacingRange').value = (obj.charSpacing || 0) / 10;
            document.getElementById('letterSpacingValue').innerText = (obj.charSpacing || 0) / 10;
            document.getElementById('outlineRange').value = obj.strokeWidth || 0;
            document.getElementById('outlineValue').innerText = obj.strokeWidth || 0;
            document.getElementById('outlineColorPicker').value = obj.stroke || "#000000";
        }

let activeTextObj = null;
        function fitTextInsideCanvas(textObj, canvas) {
            const maxWidth = canvas.width * 0.9; // leave some padding
            let charSpacing = 0; // default is 0 in Fabric.js

            // If text goes wider than canvas, keep increasing charSpacing negatively
            while (textObj.width > maxWidth && charSpacing > -200) {
                charSpacing -= 10; // closer together (negative values squeeze letters)
                textObj.set({ charSpacing });
                textObj.setCoords();
            }

            canvas.renderAll();
        }

        canvas.on('object:scaling', function (e) {
            const obj = e.target;
            const canvasWidth = canvas.width;
            const canvasHeight = canvas.height;

            obj.setCoords();
            const boundingRect = obj.getBoundingRect(true);

            // If object goes outside, undo scaling
            if (boundingRect.left < 0 ||
                boundingRect.top < 0 ||
                boundingRect.left + boundingRect.width > canvasWidth ||
                boundingRect.top + boundingRect.height > canvasHeight) {
                obj.scaleX = obj.lastGoodScaleX || obj.scaleX;
                obj.scaleY = obj.lastGoodScaleY || obj.scaleY;
            } else {
                obj.lastGoodScaleX = obj.scaleX;
                obj.lastGoodScaleY = obj.scaleY;
            }

            canvas.renderAll();
        });


        document.querySelector('.text_panel_open_btn').addEventListener('click', function () {
            let textValue = document.getElementById('editTextArea').textContent.trim();
            if (!textValue) return;

            let text = new fabric.Textbox(textValue, {
                fontSize: 44,
                fontFamily: 'Arial',
                fill: '#000000',
                fontWeight: 'bold',
                editable: true,
                selectable: true,
                textAlign: 'center',   // center align inside textbox
                // width: canvas.width 
            });

            // Add to canvas first
            canvas.add(text);
            addDeleteControl(text);

            // Center horizontally and vertically on canvas
            canvas.centerObject(text);
            

            // Update render
            canvas.setActiveObject(text);
            canvas.renderAll();
            fitTextInsideCanvas(text, canvas);

            addLayerToList(text, "textbox");  // 👈 here

            let sideKey = "";
            if (currentView === "front") sideKey = "front";
            else if (currentView === "back") sideKey = "back";
            else if (currentView === "left_sleeve") sideKey = "left_sleeve";
            else if (currentView === "right_sleeve") sideKey = "right_sleeve";
            text.sideKey = sideKey;

            designedSides[sideKey].designed = true;
            updateSidePricing();


            activeTextObj = text;

            // Switch panel to Edit Mode
            document.getElementById('textInputBox').style.display = 'none';
            document.getElementById('editTextOptions').style.display = 'block';
            document.getElementById('fontFamilySelect').style.display = 'block';
            document.getElementById('textShapeSelect').style.display = 'block';
            document.getElementById('textPanelTitle').innerText = "Edit Text";
            document.getElementById('editTextArea').value = textValue;

            // === Cart Integration for Text ===
            // const textPrice = 3.00; // fixed price for each text added
            // const design_id = "custom_text";

            // $('.add_to_cart_error').hide();

            // if ($('#mock_flip').val() == "Show Back View") {
            //     $("#fornt_design_id").val(design_id);

            //     let currentPrice = parseFloat($("#fornt_design_price").val()) || 0;
            //     let newPrice = currentPrice + textPrice;

            //     $("#fornt_design_price").val(newPrice);
            //     $('.dynamic_price_fornt').text(newPrice.toFixed(2));
            //     total_calc();
            // } else {
            //     $("#back_design_id").val(design_id);

            //     let currentPrice = parseFloat($("#back_design_price").val()) || 0;
            //     let newPrice = currentPrice + textPrice;

            //     $("#back_design_price").val(newPrice);
            //     $('.dynamic_price_back').text(newPrice.toFixed(2));
            //     total_calc();
            // }

            $('.opt_range').val(0);
        });


        canvas.on('mouse:down', function (e) {
            if (e.target && e.target.type === 'textbox') {
                activeTextObj = e.target;

                // show panel
                document.getElementById('mainMenu').style.display = 'none';
                document.getElementById('textPanel').style.display = 'block';
                document.getElementById('editTextOptions').style.display = 'block';

                // update controls with current text props
                updateControls(activeTextObj);
                // addDeleteControl(activeTextObj);
            } else {
                activeTextObj = null;
                // agar dusri jagah click ho to panel hide karna hai?
                // document.getElementById('textPanel').style.display = 'none';
            }
        });




        /* ===== Controls ===== */
        document.getElementById('editTextArea').addEventListener('input', function () {
    let obj = canvas.getActiveObject();
    if (obj && obj.type === 'textbox') {
        obj.text = this.value;

        // Run fitting logic again
        fitTextInsideCanvas(obj, canvas);

        // Keep centered
        canvas.centerObject(obj);

        // ✅ Update layers panel
        let layerItem = document.getElementById(obj.layerId);
        if (layerItem) {
            let thumbText = layerItem.querySelector(".layer-thumb-text");
            if (thumbText) {
                thumbText.textContent = `"${obj.text}"`;
            }
        }
        

        canvas.renderAll();
    }
});

        let clipboard = null;

        // Listen for keyboard events
        document.addEventListener('keydown', function (e) {
            let activeObj = canvas.getActiveObject();

            // Delete key → remove object
            if (e.key === "Delete") {
                if (activeObj) {
                    canvas.remove(activeObj);
                    canvas.discardActiveObject();
                    canvas.renderAll();
                }
            }

            // Ctrl + C → copy
            if (e.ctrlKey && e.key.toLowerCase() === 'c') {
                if (activeObj) {
                    activeObj.clone(function (cloned) {
                        clipboard = cloned;
                    });
                }
            }

            // Ctrl + V → paste
            if (e.ctrlKey && e.key.toLowerCase() === 'v') {
                if (clipboard) {
                    clipboard.clone(function (clonedObj) {
                        canvas.discardActiveObject();

                        // Offset pasted object so it doesn’t overlap exactly
                        clonedObj.set({
                            left: clonedObj.left + 20,
                            top: clonedObj.top + 20,
                            evented: true
                        });

                        if (clonedObj.type === 'activeSelection') {
                            // If it’s a group, add objects individually
                            clonedObj.canvas = canvas;
                            clonedObj.forEachObject(function (obj) {
                                canvas.add(obj);
                                addLayerToList(obj, obj.type); // 👈 detect each object's type
                            });
                            clonedObj.setCoords();
                        } else {
                            canvas.add(clonedObj);
                            addLayerToList(clonedObj, clonedObj.type); // 👈 detect type dynamically
                        }

                        clipboard.top += 20;
                        clipboard.left += 20;

                        canvas.setActiveObject(clonedObj);
                        canvas.renderAll();
                    });
                }
            }
        });



        function fitTextInsideCanvas(textObj, canvas) {
            const maxWidth = canvas.width * 0.9; // padding
            const maxHeight = canvas.height * 0.9;

            // Reset scaling so measurements are correct
            textObj.scaleX = 1;
            textObj.scaleY = 1;

            textObj.setCoords();

            // If width is too large → shrink
            let scaleX = maxWidth / textObj.width;
            let scaleY = maxHeight / textObj.height;

            let scale = Math.min(1, scaleX, scaleY);

            if (scale < 1) {
                textObj.scaleX = scale;
                textObj.scaleY = scale;
                textObj.setCoords();
            }

            canvas.renderAll();
        }


        document.getElementById('fontFamilySelect').addEventListener('change', function () {
            let obj = canvas.getActiveObject();
            if (obj && obj.type === 'textbox') {
                let newFont = this.value;
                // Ensure font is loaded before applying
                document.fonts.load(`16px "${newFont}"`).then(function () {
                    obj.set('fontFamily', newFont);
                    canvas.renderAll();
                }).catch(function () {
                    obj.set('fontFamily', newFont);
                    canvas.renderAll();
                });
            }
        });

        const originalTextObjects = new Map()

function applyTextShape(obj, shapeType) {
  if (!obj || obj.type !== "textbox") return

  if (shapeType === "normal") {
    if (originalTextObjects.has(obj.id)) {
      const original = originalTextObjects.get(obj.id)
      canvas.remove(obj)
      canvas.add(original)
      canvas.setActiveObject(original)
      originalTextObjects.delete(obj.id)
      canvas.renderAll()
    }
    return
  }

  if (!originalTextObjects.has(obj.id)) {
    originalTextObjects.set(obj.id, obj)
  }

  const text = obj.text
  if (!text || text.length === 0) return

  const fontSize = obj.fontSize || 30
  const fontFamily = obj.fontFamily || "Arial"
  const fill = obj.fill || "#000000"

  const charCount = text.length
  const estimatedCharWidth = fontSize * 0.6
  const totalTextWidth = charCount * estimatedCharWidth

  const radius =
    shapeType === "circle" ? totalTextWidth / (2 * Math.PI) + fontSize : totalTextWidth / Math.PI + fontSize / 2

  const group = new fabric.Group([], {
    left: obj.left,
    top: obj.top,
    selectable: true,
    id: obj.id, // Preserve ID for state management
  })

  for (let i = 0; i < text.length; i++) {
    const char = text[i]

    const charObj = new fabric.Text(char, {
      fontFamily: fontFamily,
      fill: fill,
      fontSize: fontSize,
      fontWeight: obj.fontWeight || "normal",
      fontStyle: obj.fontStyle || "normal",
    })

    const charWidth = charObj.width
    let x, y, angle

    if (shapeType === "arc") {
      const totalAngle = Math.PI
      const startAngle = -Math.PI / 2 // Start at top
      angle = startAngle + (i / (charCount - 1 || 1)) * totalAngle

      x = radius * Math.cos(angle)
      y = radius * Math.sin(angle)

      charObj.angle = (angle * 180) / Math.PI + 90
    } else if (shapeType === "circle") {
      const totalAngle = 2 * Math.PI
      angle = (i / charCount) * totalAngle - Math.PI / 2 // Start at top

      x = radius * Math.cos(angle)
      y = radius * Math.sin(angle)

      charObj.angle = (angle * 180) / Math.PI + 90
    } else if (shapeType === "wave") {
      const frequency = 0.5 // Wave cycles per character
      const amplitude = fontSize * 0.8 // Wave height

      x = i * (charWidth + 2) // Proper character spacing
      y = Math.sin(i * frequency) * amplitude

      charObj.angle = Math.cos(i * frequency) * 10
    } else if (shapeType === "flag") {
      const frequency = 0.4
      const amplitude = (i / charCount) * fontSize * 1.2 // Progressive amplitude

      x = i * (charWidth + 2)
      y = Math.sin(i * frequency) * amplitude

      charObj.angle = Math.sin(i * frequency) * (i / charCount) * 20
    }

    charObj.left = x
    charObj.top = y

    group.addWithUpdate(charObj)
  }

  group.set({
    originX: "center",
    originY: "center",
    left: obj.left + obj.width / 2,
    top: obj.top + obj.height / 2,
  })

  canvas.remove(obj)
  canvas.add(group)
  canvas.setActiveObject(group)
  canvas.renderAll()
}

document.getElementById("textShapeSelect").addEventListener("change", function () {
  const obj = canvas.getActiveObject()
  const shapeType = this.value

  if (!obj) {
    console.warn("No object selected")
    return
  }

  if (obj.type === "textbox") {
    applyTextShape(obj, shapeType)
  } else if (obj.type === "group" && originalTextObjects.has(obj.id)) {
    const original = originalTextObjects.get(obj.id)
    canvas.remove(obj)
    canvas.add(original)
    canvas.setActiveObject(original)
    originalTextObjects.delete(obj.id)

    if (shapeType !== "normal") {
      applyTextShape(original, shapeType)
    }
    canvas.renderAll()
  } else {
    console.warn("Selected object is not a textbox")
  }
})


        document.getElementById('fontColorPicker').addEventListener('input', function () {
            let obj = canvas.getActiveObject();
            if (obj && obj.type === 'textbox') {
                obj.set('fill', this.value);
                canvas.renderAll();
            }
        });

        document.getElementById('letterSpacingRange').addEventListener('input', function () {
            let obj = canvas.getActiveObject();
            if (obj && obj.type === 'textbox') {
                obj.set('charSpacing', this.value * 10);
                document.getElementById('letterSpacingValue').innerText = this.value;
                canvas.renderAll();
            }
        });
document.getElementById('FontRange').addEventListener('input', function () {
    let obj = canvas.getActiveObject();
    if (!obj || obj.type !== 'textbox') return;

    let newSize = parseInt(this.value, 10);
    let currentSize = obj.fontSize;

    if (newSize < currentSize) {
        // Always allow decreasing
        obj.fontSize = newSize;
        obj.scaleX = 1;
        obj.scaleY = 1;
        obj.setCoords();
    } else {
        // Try increasing
        obj.fontSize = newSize;
        obj.scaleX = 1;
        obj.scaleY = 1;
        obj.setCoords();

        let objWidth = obj.getScaledWidth();
        let objHeight = obj.getScaledHeight();
        let canvasWidth = canvas.width;
        let canvasHeight = canvas.height;

        // Block increase only if it would go outside
        if (
            obj.left + objWidth > canvasWidth ||
            obj.left < 0 ||
            obj.top + objHeight > canvasHeight ||
            obj.top < 0
        ) {
            obj.fontSize = currentSize; // revert
            obj.scaleX = 1;
            obj.scaleY = 1;
            obj.setCoords();
        }
    }

    // Horizontally center only
    canvas.centerObjectH(obj);
    obj.setCoords();
    canvas.renderAll();

    document.getElementById('FontRangeValue').innerText = obj.fontSize;
});









        document.getElementById('outlineRange').addEventListener('input', function () {
            let obj = canvas.getActiveObject();
            if (obj && obj.type === 'textbox') {
                obj.set('strokeWidth', parseInt(this.value));
                document.getElementById('outlineValue').innerText = this.value;
                canvas.renderAll();
            }
        });


        document.getElementById('outlineColorPicker').addEventListener('input', function () {
            let obj = canvas.getActiveObject();
            if (obj && obj.type === 'textbox') {
                obj.set('stroke', this.value);
                canvas.renderAll();
            }
        });



        let copiedObject = null;

        /* Flip Horizontal */
        document.getElementById('flipHBtn').addEventListener('click', function () {
            let obj = canvas.getActiveObject();
            if (obj) {
                obj.toggle('flipX');
                canvas.renderAll();
            }
        });

        /* Flip Vertical */
        document.getElementById('flipVBtn').addEventListener('click', function () {
            let obj = canvas.getActiveObject();
            if (obj) {
                obj.toggle('flipY');
                canvas.renderAll();
            }
        });

        /* Center Horizontal */
        document.getElementById('centerHBtn').addEventListener('click', function () {
            let obj = canvas.getActiveObject();
            if (obj) {
                canvas.centerObjectH(obj);
                canvas.renderAll();
            }
        });

        /* Center Vertical */
        document.getElementById('centerVBtn').addEventListener('click', function () {
            let obj = canvas.getActiveObject();
            if (obj) {
                canvas.centerObjectV(obj);
                canvas.renderAll();
            }
        });

        /* Copy */
        document.getElementById('copyBtn').addEventListener('click', function () {
            let obj = canvas.getActiveObject();
            if (obj) {
                obj.clone(function (cloned) {
                    copiedObject = cloned;
                });
            }
        });

        /* Paste */
        document.getElementById('pasteBtn').addEventListener('click', function () {
            if (copiedObject) {
                copiedObject.clone(function (clone) {
                    clone.set({
                        left: clone.left + 20, // offset to avoid exact overlap
                        top: clone.top + 20,
                        evented: true,
                    });
                    canvas.add(clone);
                    addLayerToList(clone, 'textbox')
                    canvas.setActiveObject(clone);
                    canvas.renderAll();
                    activeTextObj = clone; // update your active text reference
                });
            }
        });





        $("#avatarlist").on('click', ".img-polaroid", function (e) {
            var json = canvas.toJSON();
            // canvas.clear();
            appar_close()

            var el = e.target;
            var price = parseFloat($(this).data('price')) || 0;
            var design_id = $(this).data('designid')

            var offset = 50;
            var left = fabric.util.getRandomInt(0 + offset, 200 - offset);
            var top = fabric.util.getRandomInt(0 + offset, 400 - offset);
            var angle = fabric.util.getRandomInt(-20, 40);
            var width = fabric.util.getRandomInt(30, 50);
            var opacity = (function (min, max) { return Math.random() * (max - min) + min; })(0.5, 1);

            fabric.Image.fromURL(el.src, function (image) {
                image.set({
                    left: 20,
                    top: 60,
                    angle: 0,
                    padding: 10,
                    cornersize: 15,
                    hasRotatingPoint: true,
                    selectable: true
                });
                image.scaleToHeight(200);
                image.scaleToWidth(190);

                canvas.add(image);
                addDeleteControl(image);
            });

            var obj = {
                'src': el.src,
                'price': parseFloat(price)
            }

            $('.add_to_cart_error').hide()

            if ($('#mock_flip').val() == "Show Back View") {
                $("#fornt_design_id").val(design_id)
                let currentPrice = parseFloat($("#fornt_design_price").val()) || 0;
                let newPrice = currentPrice + price;

                $("#fornt_design_price").val(newPrice);
                $('.dynamic_price_fornt').text(newPrice.toFixed(2));
                total_calc()


            } else {

                $("#back_design_id").val(design_id)
                let currentPrice = parseFloat($("#back_design_price").val()) || 0;
                let newPrice = currentPrice + price;



                $("#back_design_price").val(newPrice);
                $('.dynamic_price_back').text(newPrice.toFixed(2));
                total_calc()

            }

            $('.opt_range').val(0)


        });


        $("#clear-polaroid").click(function (e) {
            var json = canvas.toJSON();
            canvas.clear();
            appar_close()

            var price = 0


            fabric.Image.fromURL('', function (image) {
                image.set({
                    left: 100,
                    top: 140,
                    angle: 0,
                    padding: 10,
                    cornersize: 15,
                    hasRotatingPoint: true,
                    selectable: false
                });
                image.scaleToHeight(220);
                image.scaleToWidth(220);
                canvas.add(image);
            });

            var obj = {
                'src': '',
                'price': parseFloat(price)
            }


            if ($('#mock_flip').val() == "Show Back View") {
                $("#fornt_design_id").val('')
                $("#fornt_design_price").val(price)
                $('.dynamic_price_fornt').text(price)
                total_calc()


            } else {

                $("#back_design_id").val('')
                $("#back_design_price").val(price)
                $('.dynamic_price_back').text(price)
                total_calc()

            }


        });

        //   document.getElementById('remove-selected').onclick = function() {		  
        // 	    var activeObject = canvas.getActiveObject(),
        // 	        activeGroup = canvas.getActiveGroup();

        // 	    if (activeObject) {
        // 			if (activeObject.get('type') === "text"){
        // 				if ($('#mock_flip').val() == "Show Back View") {
        // 					$('.dynamic_price_text_fornt').text(0)
        // 					$('#text_print_front_price').val(0)
        // 					$('#text_print_front').val("")
        // 					total_calc()

        // 				}else{
        // 					$('.dynamic_price_text_back').text(0)
        // 					$('#text_print_back_price').val(0)
        // 					$('#text_print_back').val("")
        // 					total_calc()
        // 				}
        // 			}
        // 			canvas.remove(activeObject);
        // 			$("#text-string").val("");

        // 	    }
        // 	    else if (activeGroup) {
        // 	      var objectsInGroup = activeGroup.getObjects();
        // 	      canvas.discardActiveGroup();
        // 	      objectsInGroup.forEach(function(object) {
        // 			if (object.get('type') === "text"){
        // 				if ($('#mock_flip').val() == "Show Back View") {
        // 					$('#text_print_front').val("")
        // 					$('#text_print_front_price').val(0)
        // 					$('.dynamic_price_text_fornt').text(0)
        // 					total_calc()

        // 				}else{
        // 					$('#text_print_back').val("")
        // 					$('#text_print_back_price').val(0)
        // 					$('.dynamic_price_text_back').text(0)
        // 					total_calc()
        // 				}
        // 			}
        // 	        canvas.remove(object);

        // 	      });
        // 	    }

        // 		$('.opt_range').val(0)


        // 		if ($('#mock_flip').val() == "Show Back View") {
        // 			$("#fornt_design_id").val('')
        // 			$("#fornt_design_price").val(0)
        // 			$('.dynamic_price_fornt').text(0)
        // 			total_calc()

        // 		}else{

        // 			$("#back_design_id").val('')
        // 			$("#back_design_price").val(0)
        // 			$('.dynamic_price_back').text(0)
        // 			total_calc()

        // 		}

        //   };
        //   document.getElementById('bring-to-front').onclick = function() {		  
        // 	    var activeObject = canvas.getActiveObject(),
        // 	        activeGroup = canvas.getActiveGroup();
        // 	    if (activeObject) {
        // 	      activeObject.bringToFront();
        // 	    }
        // 	    else if (activeGroup) {
        // 	      var objectsInGroup = activeGroup.getObjects();
        // 	      canvas.discardActiveGroup();
        // 	      objectsInGroup.forEach(function(object) {
        // 	        object.bringToFront();
        // 	      });
        // 	    }
        //   };
        //   document.getElementById('send-to-back').onclick = function() {		  
        // 	    var activeObject = canvas.getActiveObject(),
        // 	        activeGroup = canvas.getActiveGroup();
        // 	    if (activeObject) {
        // 	      activeObject.sendToBack();
        // 	    }
        // 	    else if (activeGroup) {
        // 	      var objectsInGroup = activeGroup.getObjects();
        // 	      canvas.discardActiveGroup();
        // 	      objectsInGroup.forEach(function(object) {
        // 	        object.sendToBack();
        // 	      });
        // 	    }
        //   };		  
        //   $("#text-bold").click(function() {		  
        // 	  var activeObject = canvas.getActiveObject();
        // 	  if (activeObject && activeObject.type === 'text') {
        // 	    activeObject.fontWeight = (activeObject.fontWeight == 'bold' ? '' : 'bold');		    
        // 	    canvas.renderAll();
        // 	  }
        // 	});
        //   $("#text-italic").click(function() {		 
        // 	  var activeObject = canvas.getActiveObject();
        // 	  if (activeObject && activeObject.type === 'text') {
        // 		  activeObject.fontStyle = (activeObject.fontStyle == 'italic' ? '' : 'italic');		    
        // 	    canvas.renderAll();
        // 	  }
        // 	});
        //   $("#text-strike").click(function() {		  
        // 	  var activeObject = canvas.getActiveObject();
        // 	  if (activeObject && activeObject.type === 'text') {
        // 		  activeObject.textDecoration = (activeObject.textDecoration == 'line-through' ? '' : 'line-through');
        // 	    canvas.renderAll();
        // 	  }
        // 	});
        //   $("#text-underline").click(function() {		  
        // 	  var activeObject = canvas.getActiveObject();
        // 	  if (activeObject && activeObject.type === 'text') {
        // 		  activeObject.textDecoration = (activeObject.textDecoration == 'underline' ? '' : 'underline');
        // 	    canvas.renderAll();
        // 	  }
        // 	});
        //   $("#text-left").click(function() {		  
        // 	  var activeObject = canvas.getActiveObject();
        // 	  if (activeObject && activeObject.type === 'text') {
        // 		  activeObject.textAlign = 'left';
        // 	    canvas.renderAll();
        // 	  }
        // 	});
        //   $("#text-center").click(function() {		  
        // 	  var activeObject = canvas.getActiveObject();
        // 	  if (activeObject && activeObject.type === 'text') {
        // 		  activeObject.textAlign = 'center';		    
        // 	    canvas.renderAll();
        // 	  }
        // 	});
        //   $("#text-right").click(function() {		  
        // 	  var activeObject = canvas.getActiveObject();
        // 	  if (activeObject && activeObject.type === 'text') {
        // 		  activeObject.textAlign = 'right';		    
        // 	    canvas.renderAll();
        // 	  }
        // 	});	  
        //   $("#font-family").change(function() {
        //       var activeObject = canvas.getActiveObject();
        //       if (activeObject && activeObject.type === 'text') {
        //         activeObject.fontFamily = this.value;
        //         canvas.renderAll();
        //       }
        //     });	  
        // 	$('#text-bgcolor').miniColors({
        // 		change: function(hex, rgb) {
        // 		  var activeObject = canvas.getActiveObject();
        // 	      if (activeObject && activeObject.type === 'text') {
        // 	    	  activeObject.backgroundColor = this.value;
        // 	        canvas.renderAll();
        // 	      }
        // 		},
        // 		open: function(hex, rgb) {
        // 			//
        // 		},
        // 		close: function(hex, rgb) {
        // 			//
        // 		}
        // 	});		
        // 	$('#text-fontcolor').miniColors({
        // 		change: function(hex, rgb) {
        // 		  var activeObject = canvas.getActiveObject();
        // 	      if (activeObject && activeObject.type === 'text') {
        // 	    	  activeObject.fill = this.value;
        // 	    	  canvas.renderAll();
        // 	      }
        // 		},
        // 		open: function(hex, rgb) {
        // 			//
        // 		},
        // 		close: function(hex, rgb) {
        // 			//
        // 		}
        // 	});

        // 	$('#text-strokecolor').miniColors({
        // 		change: function(hex, rgb) {
        // 		  var activeObject = canvas.getActiveObject();
        // 	      if (activeObject && activeObject.type === 'text') {
        // 	    	  activeObject.strokeStyle = this.value;
        // 	    	  canvas.renderAll();
        // 	      }
        // 		},
        // 		open: function(hex, rgb) {
        // 			//
        // 		},
        // 		close: function(hex, rgb) {
        // 			//
        // 		}
        // 	});

        //canvas.add(new fabric.fabric.Object({hasBorders:true,hasControls:false,hasRotatingPoint:false,selectable:false,type:'rect'}));
        //    $("#drawingArea").hover(
        //         function() { 	        	
        //         	 canvas.add(line1);
        // 	         canvas.add(line2);
        // 	         canvas.add(line3);
        // 	         canvas.add(line4); 
        // 	         canvas.renderAll();
        //         },
        //         function() {	        	
        //         	 canvas.remove(line1);
        // 	         canvas.remove(line2);
        // 	         canvas.remove(line3);
        // 	         canvas.remove(line4);
        // 	         canvas.renderAll();
        //         }
        //     );

        $('.color-preview').click(function () {
            var color = $(this).css("background-color");
            document.getElementById("shirtDiv").style.backgroundColor = color;
            $('.color-preview').removeClass("active_color");
            $(this).addClass("active_color");


        });

        // $('.color-preview').click(function(){
        // 	var shirtImage = $(this).attr("data-image"); 
        // 	$("#tshirtFacing").attr("src", shirtImage);

        // 	$('.color-preview').removeClass("active_color");
        // 	$(this).addClass("active_color");
        // 	});


        function calc() {

        }


$('.main_btn_for_front_back .flip_btn').click(function () {
    let targetView = $(this).data('btntype');
    changeSide(targetView);
});

function changeSide(targetView) {
    if (targetView === currentView) return;

    saveCurrentCanvasState(currentView);
    canvas.clear();

    let jsonData = "";
    let mockupImg = "";

    if (targetView === "front") {
        jsonData = a;
        mockupImg = $("#front_mockup_img_preview").val();
    } else if (targetView === "back") {
        jsonData = b;
        mockupImg = $("#back_mockup_img").val();
    } else if (targetView === "left_sleeve") {
        jsonData = c;
        mockupImg = $("#left_mockup_img").val();
    } else if (targetView === "right_sleeve") {
        jsonData = d;
        mockupImg = $("#right_mockup_img").val();
    }

    $("#tshirtFacing").attr("src", mockupImg);

    if (jsonData) {
        canvas.loadFromJSON(jsonData, function () {
            canvas.renderAll();
            rebuildLayerList();
        });
    } else {
        rebuildLayerList();
    }

    $(".main_btn_for_front_back .flip_btn").removeClass("clickdisabled");
    $(`[data-btntype='${targetView}']`).addClass("clickdisabled");

    currentView = targetView;
    setTimeout(() => canvas.calcOffset(), 200);
}

function saveCurrentCanvasState(view) {
    
    // const json = JSON.stringify(canvas);
    const json = JSON.stringify(canvas.toJSON(['sideKey', 'customData', 'layerId'])); 
    if (view === "front") a = json;
    else if (view === "back") b = json;
    else if (view === "left_sleeve") c = json;
    else if (view === "right_sleeve") d = json;
}

function rebuildLayerList() {
    $("#layersList").empty();
    canvas.getObjects().forEach(obj => {
        let type = (obj.type === "text" || obj.type === "i-text" || obj.type === "textbox") ? "textbox" : "image";
        if (!obj.layerId) obj.layerId = "layer_" + (++layerIdCounter);
        addLayerToList(obj, type);
    });
}

        // });




        $(".clearfix button,a").tooltip();
        line1 = new fabric.Line([0, 0, 200, 0], { "stroke": "#000000", "strokeWidth": 1, hasBorders: false, hasControls: false, hasRotatingPoint: false, selectable: false });
        line2 = new fabric.Line([199, 0, 200, 299], { "stroke": "#000000", "strokeWidth": 1, hasBorders: false, hasControls: false, hasRotatingPoint: false, selectable: false });
        line3 = new fabric.Line([0, 0, 0, 300], { "stroke": "#000000", "strokeWidth": 1, hasBorders: false, hasControls: false, hasRotatingPoint: false, selectable: false });
        line4 = new fabric.Line([0, 300, 200, 299], { "stroke": "#000000", "strokeWidth": 1, hasBorders: false, hasControls: false, hasRotatingPoint: false, selectable: false });
    };


    function getRandomNum(min, max) {
        return Math.random() * (max - min) + min;
    }

    function onObjectSelected(e) {
        var selectedObject = e.target;
        $("#text-string").val("");
        selectedObject.hasRotatingPoint = true
        if (selectedObject && selectedObject.type === 'text') {
            //display text editor	    	
            $("#texteditor").css('display', 'block');
            $("#text-string").val(selectedObject.getText());
            $('#text-fontcolor').miniColors('value', selectedObject.fill);
            $('#text-strokecolor').miniColors('value', selectedObject.strokeStyle);
            $("#imageeditor").css('display', 'block');
        }
        else if (selectedObject && selectedObject.type === 'image') {
            //display image editor
            $("#texteditor").css('display', 'none');
            $("#imageeditor").css('display', 'block');
        }
    }
    function onSelectedCleared(e) {
        $("#texteditor").css('display', 'none');
        $("#text-string").val("");
        $("#imageeditor").css('display', 'none');
    }
    function setFont(font) {
        var activeObject = canvas.getActiveObject();
        if (activeObject && activeObject.type === 'text') {
            activeObject.fontFamily = font;
            canvas.renderAll();
        }
    }
    function removeWhite() {
        var activeObject = canvas.getActiveObject();
        if (activeObject && activeObject.type === 'image') {
            activeObject.filters[2] = new fabric.Image.filters.RemoveWhite({ hreshold: 100, distance: 10 });//0-255, 0-255
            activeObject.applyFilters(canvas.renderAll.bind(canvas));
        }
    }


    $(".sizeselect , .mycolor").change(function () {

        $('.qty').val(parseInt($('.qty').data('min')));
    })


    $('.qty').on('change', function () {
        var qty_min = parseInt($(this).data('min'))
        var sizeava = parseInt($('#Ava_num').val())
        var this_val = $(this).val()

        if (this_val < qty_min) {
            $(this).val(qty_min)
        }

        if (parseInt(this_val) > parseInt(sizeava)) {
            $(this).val(sizeava)
        }


    })


    $('.value-plus').on('click', function () {

        var sizeava = parseInt($('#Ava_num').val())


        var divUpd = $('.qty'), newVal = parseInt(divUpd.val(), 10) + 1;
        divUpd.val(newVal);

        if (divUpd.val() >= sizeava) {
            $(".value").css({ "border": "1px solid #ff0505" });
            $('.add_to_cart_error').html('Sorry, you can only purchase allowable "' + sizeava + '" quantity of this product.').show();
            //$('.error').html('Sorry, you can only purchase allowable "'+sizeava+'" quantity of this product.').delay(4000).fadeOut();
            $('.qty').val(sizeava);
            setTimeout(function () {
                $('.add_to_cart_error').hide()
                $(".value").css({ "border": "1px solid #a7a7a7" });
            }, 2000)
        }

        total_calc()



    });

    $('.value-minus').on('click', function () {

        var qty_min = parseInt($('.qty').data('min'))
        var divUpd = $('.qty'),
            newVal = parseInt(divUpd.val(), 10) - 1;

        if (newVal >= qty_min) {
            divUpd.val(newVal);
        }

        var max_val = parseInt($('#Ava_num').val())
        if (divUpd.val() < max_val) {
            $(".value").css({ "border": "1px solid #a7a7a7" });

        }

        total_calc()
    });




    function total_calc() {

        var front_price = $('#fornt_design_price').val()
        var back_price = $('#back_design_price').val()

        var front_text_price = $('#text_print_front_price').val()
        var back_text_price = $('#text_print_back_price').val()

        var get_mockup_price = $('#mockup_price_for_calc').val()

        // var qty = $('.qty').val()
        var add_desgin_price = parseFloat(front_price) + parseFloat(back_price) + parseFloat(front_text_price) + parseFloat(back_text_price)
        var gen_total = parseFloat(get_mockup_price) + add_desgin_price

        console.log('total', front_price, back_price, front_text_price, back_text_price, get_mockup_price, add_desgin_price, gen_total);
        

        var grand_total = gen_total

        $('#mockup_price').val(gen_total)
        $('.dynamic_price_total').text(grand_total)


    }



    function appar_open() {
        if (window.screen.width < 800) {
            $(".apparance_panel").css({ 'transform': 'translateX(0px)' })
        }
    }

    function appar_close() {
        if (window.screen.width < 800) {
            $(".apparance_panel").css({ 'transform': 'translateX(300px)' })
        }
    }


