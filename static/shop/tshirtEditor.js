var canvas;
var tshirts = new Array(); //prototype: [{style:'x',color:'white',front:'a',back:'b',price:{tshirt:'12.95',frontPrint:'4.99',backPrint:'4.99',total:'22.47'}}]
var a;
var b;
var line1;
var line2;
var line3;
var line4;

	
 	$(document).ready(function() {
		//setup front side canvas 
 		canvas = new fabric.Canvas('tcanvas', {
		  hoverCursor: 'pointer',
		  selection: true,
		
		  selectionBorderColor:'blue'
		});

		



		$('#sizechange').change(function(){
			var sizeval = $(this).val()
			$('#size_num').text(sizeval)
			var activeObject = canvas.getActiveObject(),
			activeGroup = canvas.getActiveGroup();
			if (activeObject) {
				var min_size = 150;
				var puls_size = min_size + parseInt(sizeval)
				activeObject.scaleToHeight(puls_size)
				activeObject.scaleToWidth(puls_size)


			}
			else if (activeGroup) {
				var objectsInGroup = activeGroup.getObjects();
				canvas.discardActiveGroup();
				objectsInGroup.forEach(function(object) {
					// canvas.remove(object);
					var min_size = 150;
					var puls_size = min_size + parseInt(sizeval)
					
					object.scaleToHeight(puls_size)
					object.scaleToWidth(puls_size)
				});
			}
			else{
				$(this).val(0)
				$('#size_num').text(0)
			}

			canvas.renderAll();
		})


		$('#move_hr').change(function(){
			// console.log('work')
			var hrval = $(this).val()
			$('#move_hr_num').text(hrval)
			var activeObject = canvas.getActiveObject(),
			activeGroup = canvas.getActiveGroup();
			if (activeObject) {
				var min_move = 100;
				var puls_left = min_move + parseInt(hrval)
			
				activeObject.set({ 
					left: puls_left,
				});

			}
			else if (activeGroup) {
				var objectsInGroup = activeGroup.getObjects();
				canvas.discardActiveGroup();
				objectsInGroup.forEach(function(object) {
					var min_move= 100;
					var puls_left = min_move + parseInt(hrval)
					object.set({ 
						left: puls_left,
					});

				});
			}
			else{
				$(this).val(0)
				$('#move_hr_num').text(0)
			}

			canvas.renderAll();
		})




		$('#move_vr').change(function(){
			// console.log('work')
			var vrval = $(this).val()
			$('#move_vr_num').text(vrval)
			var activeObject = canvas.getActiveObject(),
			activeGroup = canvas.getActiveGroup();
			if (activeObject) {
				var min_move = 100;
				var puls_top = min_move + parseInt(vrval)
			
				activeObject.set({ 
					top: puls_top,
				});

			}
			else if (activeGroup) {
				var objectsInGroup = activeGroup.getObjects();
				canvas.discardActiveGroup();
				objectsInGroup.forEach(function(object) {
					var min_move = 100;
					var puls_top = min_move + parseInt(vrval)
					object.set({ 
				
						top: puls_top,
						
					});

				});
			}
			else{
				$(this).val(0)
				$('#move_vr_num').text(0)
			}

			canvas.renderAll();
		})



		$('#rotate_slider').change(function(){
			// console.log('work')
			var rotval = $(this).val()

			$('#move_rot_num').text(rotval)

			var activeObject = canvas.getActiveObject(),
			activeGroup = canvas.getActiveGroup();
			if (activeObject) {
				var min_rotate = 0;
				var puls_rotate = min_rotate + parseInt(rotval)
			
				activeObject.set({ 
					angle: puls_rotate,
				});

			}
			else if (activeGroup) {
				var objectsInGroup = activeGroup.getObjects();
				canvas.discardActiveGroup();
				objectsInGroup.forEach(function(object) {
					var min_rotate = 0;
					var puls_rotate = min_rotate + parseInt(rotval)
					object.set({ 
				
						angle: puls_rotate,
						
					});

				});
			}
			else{
				$(this).val(0)
				$('#move_rot_num').text(0)
			}

			canvas.renderAll();
		})
		
		

 		canvas.on({
			 'object:moving': function(e) {		  	
			    e.target.opacity = 0.5;
			  },
			  'object:modified': function(e) {		  	
			    e.target.opacity = 1;
				
			  },
			  
			 'object:selected':onObjectSelected,
			 'selection:cleared':onSelectedCleared
		 });


		 



		// piggyback on `canvas.findTarget`, to fire "object:over" and "object:out" events
 		canvas.findTarget = (function(originalFn) {
		  return function() {
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

 		canvas.on('object:over', function(e) {		
		//   e.target.setFill('red');
		//   canvas.renderAll();
		
		});
		
 		canvas.on('object:out', function(e) {		
		//   e.target.setFill('green');
		//   canvas.renderAll();
		});
		 		 	 
		document.getElementById('add-text').onclick = function() {
			var json = canvas.toJSON();
			canvas.clear();
			appar_close()
			var text = $("#text-string").val();

		    var textSample = new fabric.Text(text, {
		      left: 100,
		      top: 100,
		      fontFamily: 'helvetica',
		      angle: 0,
		      fill: '#000000',
		      scaleX: 0.5,
		      scaleY: 0.5,
		      fontWeight: '',
	  		  hasRotatingPoint:true
		    });	

			var text_price = $("#text_price").val()
			
            canvas.add(textSample);	
            canvas.item(canvas.item.length-1).hasRotatingPoint = true;    
            $("#texteditor").css('display', 'block');
            $("#imageeditor").css('display', 'block');
			$('.opt_range').val(0)
			

			if ($('#flip').attr("data-original-title") == "Show Back View") {
				$('#text_print_front').val(text)
				$('#text_print_front_price').val(text_price)
				$('.dynamic_price_text_fornt').text(text_price)
				total_calc()
				

			}else{
				$('#text_print_back').val(text)
				$('#text_print_back_price').val(text_price)
				$('.dynamic_price_text_back').text(text_price)
				total_calc()
			}



			
	  	};
	  	$("#text-string").keyup(function(){	  		
	  		var activeObject = canvas.getActiveObject();
		      if (activeObject && activeObject.type === 'text') {
		    	  activeObject.text = this.value;
		    	  canvas.renderAll();
		      }
	  	});
	  	$(".img-polaroid").click(function(e){
			var json = canvas.toJSON();
			canvas.clear();
			appar_close()

	  		var el = e.target;
			var price = $(this).data('price')
			var design_id = $(this).data('designid')
	  
	  		var offset = 50;
	        var left = fabric.util.getRandomInt(0 + offset, 200 - offset);
	        var top = fabric.util.getRandomInt(0 + offset, 400 - offset);
	        var angle = fabric.util.getRandomInt(-20, 40);
	        var width = fabric.util.getRandomInt(30, 50);
	        var opacity = (function(min, max){ return Math.random() * (max - min) + min; })(0.5, 1);
	        
	  		fabric.Image.fromURL(el.src, function(image) {
		          image.set({
		            left: 100,
		            top: 100,
		            angle: 0,
		            padding: 10,
		            cornersize: 15,
	      	  		hasRotatingPoint:true
		          });
				  image.scaleToHeight(150);
				  image.scaleToWidth(150);
		          canvas.add(image);
		        });
				
				var obj = {
					'src' : el.src,
					'price':parseFloat(price) 
				}
				
				$('.add_to_cart_error').hide()

				if ($('#flip').attr("data-original-title") == "Show Back View") {
					$("#fornt_design_id").val(design_id)
					$("#fornt_design_price").val(price)
					$('.dynamic_price_fornt').text(price)
					total_calc()
					

				}else{

					$("#back_design_id").val(design_id)
					$("#back_design_price").val(price)
					$('.dynamic_price_back').text(price)
					total_calc()
					
				}

				$('.opt_range').val(0)
			
			
	  	});	  		  
	  document.getElementById('remove-selected').onclick = function() {		  
		    var activeObject = canvas.getActiveObject(),
		        activeGroup = canvas.getActiveGroup();
			
		    if (activeObject) {
				if (activeObject.get('type') === "text"){
					if ($('#flip').attr("data-original-title") == "Show Back View") {
						$('.dynamic_price_text_fornt').text(0)
						$('#text_print_front_price').val(0)
						$('#text_print_front').val("")
						total_calc()
						
					}else{
						$('.dynamic_price_text_back').text(0)
						$('#text_print_back_price').val(0)
						$('#text_print_back').val("")
						total_calc()
					}
				}
				canvas.remove(activeObject);
				$("#text-string").val("");
			  
		    }
		    else if (activeGroup) {
		      var objectsInGroup = activeGroup.getObjects();
		      canvas.discardActiveGroup();
		      objectsInGroup.forEach(function(object) {
				if (object.get('type') === "text"){
					if ($('#flip').attr("data-original-title") == "Show Back View") {
						$('#text_print_front').val("")
						$('#text_print_front_price').val(0)
						$('.dynamic_price_text_fornt').text(0)
						total_calc()
						
					}else{
						$('#text_print_back').val("")
						$('#text_print_back_price').val(0)
						$('.dynamic_price_text_back').text(0)
						total_calc()
					}
				}
		        canvas.remove(object);
				
		      });
		    }

			$('.opt_range').val(0)


			if ($('#flip').attr("data-original-title") == "Show Back View") {
				$("#fornt_design_id").val('')
				$("#fornt_design_price").val(0)
				$('.dynamic_price_fornt').text(0)
				total_calc()
				
			}else{

				$("#back_design_id").val('')
				$("#back_design_price").val(0)
				$('.dynamic_price_back').text(0)
				total_calc()
				
			}

	  };
	  document.getElementById('bring-to-front').onclick = function() {		  
		    var activeObject = canvas.getActiveObject(),
		        activeGroup = canvas.getActiveGroup();
		    if (activeObject) {
		      activeObject.bringToFront();
		    }
		    else if (activeGroup) {
		      var objectsInGroup = activeGroup.getObjects();
		      canvas.discardActiveGroup();
		      objectsInGroup.forEach(function(object) {
		        object.bringToFront();
		      });
		    }
	  };
	  document.getElementById('send-to-back').onclick = function() {		  
		    var activeObject = canvas.getActiveObject(),
		        activeGroup = canvas.getActiveGroup();
		    if (activeObject) {
		      activeObject.sendToBack();
		    }
		    else if (activeGroup) {
		      var objectsInGroup = activeGroup.getObjects();
		      canvas.discardActiveGroup();
		      objectsInGroup.forEach(function(object) {
		        object.sendToBack();
		      });
		    }
	  };		  
	  $("#text-bold").click(function() {		  
		  var activeObject = canvas.getActiveObject();
		  if (activeObject && activeObject.type === 'text') {
		    activeObject.fontWeight = (activeObject.fontWeight == 'bold' ? '' : 'bold');		    
		    canvas.renderAll();
		  }
		});
	  $("#text-italic").click(function() {		 
		  var activeObject = canvas.getActiveObject();
		  if (activeObject && activeObject.type === 'text') {
			  activeObject.fontStyle = (activeObject.fontStyle == 'italic' ? '' : 'italic');		    
		    canvas.renderAll();
		  }
		});
	  $("#text-strike").click(function() {		  
		  var activeObject = canvas.getActiveObject();
		  if (activeObject && activeObject.type === 'text') {
			  activeObject.textDecoration = (activeObject.textDecoration == 'line-through' ? '' : 'line-through');
		    canvas.renderAll();
		  }
		});
	  $("#text-underline").click(function() {		  
		  var activeObject = canvas.getActiveObject();
		  if (activeObject && activeObject.type === 'text') {
			  activeObject.textDecoration = (activeObject.textDecoration == 'underline' ? '' : 'underline');
		    canvas.renderAll();
		  }
		});
	  $("#text-left").click(function() {		  
		  var activeObject = canvas.getActiveObject();
		  if (activeObject && activeObject.type === 'text') {
			  activeObject.textAlign = 'left';
		    canvas.renderAll();
		  }
		});
	  $("#text-center").click(function() {		  
		  var activeObject = canvas.getActiveObject();
		  if (activeObject && activeObject.type === 'text') {
			  activeObject.textAlign = 'center';		    
		    canvas.renderAll();
		  }
		});
	  $("#text-right").click(function() {		  
		  var activeObject = canvas.getActiveObject();
		  if (activeObject && activeObject.type === 'text') {
			  activeObject.textAlign = 'right';		    
		    canvas.renderAll();
		  }
		});	  
	  $("#font-family").change(function() {
	      var activeObject = canvas.getActiveObject();
	      if (activeObject && activeObject.type === 'text') {
	        activeObject.fontFamily = this.value;
	        canvas.renderAll();
	      }
	    });	  
		$('#text-bgcolor').miniColors({
			change: function(hex, rgb) {
			  var activeObject = canvas.getActiveObject();
		      if (activeObject && activeObject.type === 'text') {
		    	  activeObject.backgroundColor = this.value;
		        canvas.renderAll();
		      }
			},
			open: function(hex, rgb) {
				//
			},
			close: function(hex, rgb) {
				//
			}
		});		
		$('#text-fontcolor').miniColors({
			change: function(hex, rgb) {
			  var activeObject = canvas.getActiveObject();
		      if (activeObject && activeObject.type === 'text') {
		    	  activeObject.fill = this.value;
		    	  canvas.renderAll();
		      }
			},
			open: function(hex, rgb) {
				//
			},
			close: function(hex, rgb) {
				//
			}
		});
		
		$('#text-strokecolor').miniColors({
			change: function(hex, rgb) {
			  var activeObject = canvas.getActiveObject();
		      if (activeObject && activeObject.type === 'text') {
		    	  activeObject.strokeStyle = this.value;
		    	  canvas.renderAll();
		      }
			},
			open: function(hex, rgb) {
				//
			},
			close: function(hex, rgb) {
				//
			}
		});
	
		//canvas.add(new fabric.fabric.Object({hasBorders:true,hasControls:false,hasRotatingPoint:false,selectable:false,type:'rect'}));
	   $("#drawingArea").hover(
	        function() { 	        	
	        	 canvas.add(line1);
		         canvas.add(line2);
		         canvas.add(line3);
		         canvas.add(line4); 
		         canvas.renderAll();
	        },
	        function() {	        	
	        	 canvas.remove(line1);
		         canvas.remove(line2);
		         canvas.remove(line3);
		         canvas.remove(line4);
		         canvas.renderAll();
	        }
	    );
	   
	   $('.color-preview').click(function(){
		   var color = $(this).css("background-color");
		   document.getElementById("shirtDiv").style.backgroundColor = color;		 
			$('.color-preview').removeClass("active_color");
			$(this).addClass("active_color");


	   });


	   function calc(){

	   }

	   
	   $('#flip').click(
		   function() {		

			   	if ($(this).attr("data-original-title") == "Show Back View") {
					
			   		$(this).attr('data-original-title', 'Show Front View');		
					console.log('back work')
			        $("#tshirtFacing").attr("src",$("#back_mockup_img").val());			        
			        a = JSON.stringify(canvas);
			        canvas.clear();
			        try
			        {
			           var json = JSON.parse(b);
			           canvas.loadFromJSON(b);
			        }
			        catch(e)
			        {}
			        
			    } else {
			    	$(this).attr('data-original-title', 'Show Back View');
					console.log('front work')		    				    	
			    	$("#tshirtFacing").attr("src",$("#front_mockup_img_preview").val());			    	
			    	b = JSON.stringify(canvas);
			    	canvas.clear();
			    	try
			        {
			           var json = JSON.parse(a);
			           canvas.loadFromJSON(a);			           
			        }
			        catch(e)
			        {}
			    }		
			   	canvas.renderAll();
			   	setTimeout(function() {
			   		canvas.calcOffset();
			    },200);			   	
        });	   
	   $(".clearfix button,a").tooltip();
	   line1 = new fabric.Line([0,0,200,0], {"stroke":"#000000", "strokeWidth":1,hasBorders:false,hasControls:false,hasRotatingPoint:false,selectable:false});
	   line2 = new fabric.Line([199,0,200,299], {"stroke":"#000000", "strokeWidth":1,hasBorders:false,hasControls:false,hasRotatingPoint:false,selectable:false});
	   line3 = new fabric.Line([0,0,0,300], {"stroke":"#000000", "strokeWidth":1,hasBorders:false,hasControls:false,hasRotatingPoint:false,selectable:false});
	   line4 = new fabric.Line([0,300,200,299], {"stroke":"#000000", "strokeWidth":1,hasBorders:false,hasControls:false,hasRotatingPoint:false,selectable:false});
	 });//doc ready
	 
	 
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
	    	$('#text-fontcolor').miniColors('value',selectedObject.fill);
	    	$('#text-strokecolor').miniColors('value',selectedObject.strokeStyle);	
	    	$("#imageeditor").css('display', 'block');
	    }
	    else if (selectedObject && selectedObject.type === 'image'){
	    	//display image editor
	    	$("#texteditor").css('display', 'none');	
	    	$("#imageeditor").css('display', 'block');
	    }
	  }
	 function onSelectedCleared(e){
		 $("#texteditor").css('display', 'none');
		 $("#text-string").val("");
		 $("#imageeditor").css('display', 'none');
	 }
	 function setFont(font){
		  var activeObject = canvas.getActiveObject();
	      if (activeObject && activeObject.type === 'text') {
	        activeObject.fontFamily = font;
	        canvas.renderAll();
	      }
	  }
	 function removeWhite(){
		  var activeObject = canvas.getActiveObject();
		  if (activeObject && activeObject.type === 'image') {			  
			  activeObject.filters[2] =  new fabric.Image.filters.RemoveWhite({hreshold: 100, distance: 10});//0-255, 0-255
			  activeObject.applyFilters(canvas.renderAll.bind(canvas));
		  }	        
	 }




	 $('.value-plus').on('click', function () {
		
		var divUpd = $('.qty'), newVal = parseInt(divUpd.val(), 10) + 1;
		divUpd.val(newVal);
		total_calc()
		
		
	});

	$('.value-minus').on('click', function () {
		var divUpd = $('.qty'),
		newVal = parseInt(divUpd.val(), 10) - 1;
		divUpd.val(newVal);

		if ($('.qty').val() < 1){
			$(".value").css({"border" : "1px solid red"});
			$('.qty').val(1)
		}
		total_calc()
	});




	function total_calc(){

		var front_price = $('#fornt_design_price').val()
		var back_price = $('#back_design_price').val()

		var front_text_price = $('#text_print_front_price').val()
		var back_text_price = $('#text_print_back_price').val()

		var get_mockup_price = $('#mockup_price_for_calc').val()

		var qty = $('.qty').val()
		var add_desgin_price = parseFloat(front_price) + parseFloat(back_price) + parseFloat(front_text_price) + parseFloat(back_text_price)
		var gen_total =  parseFloat(get_mockup_price) + add_desgin_price

		var grand_total = gen_total * parseInt(qty)

		$('#mockup_price').val(gen_total)
		$('.dynamic_price_total').text(grand_total)


	}



	function appar_open(){
		if (window.screen.width < 800){
			$(".apparance_panel").css({'transform':'translateX(0px)'})
		}
	}
	
	function appar_close(){
		if (window.screen.width < 800){
			$(".apparance_panel").css({'transform':'translateX(300px)'})
		}
	}

	
