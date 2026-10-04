;
(function ($, document) {
  "use strict";

  var currency = $('#currency').val()
  if(!$.jStorage.storageAvailable()){
    throw 'localStorage is not available';
    return;
  }

  var $document = $(document),
    PRODUCTS_KEY = "cesta-feira-items",
    $wItemsCount = $('[data-cesta-feira-items-count]'),
    instance = null,
    defaults = {
      debug: false,
      onItemAdded: function (item) {

      },
      onItemUpdated: function (item) {

      }
    };

  /**
   * Call in the submit form event
   * @param form submit event
   */
  function submitForm(e) {
    e.preventDefault();

    var cf = $.CestaFeira();

    var $form = $(e.currentTarget),
      $submit = $form.find('[data-cesta-feira-submit]'),
      $item = $form.find('[data-cesta-feira-item-id]');

    if ( !$submit.length ) {
      $submit = $form.find( 'input[type=submit], button' ).first();
    }

    var products = $.extend( {}, $.jStorage.get( PRODUCTS_KEY ) ), action, serializedObject = serializeObject($form);

    if(!($item.val() in products)){

      action = "added";

      // Call callback for items added
      cf.defaults.onItemAdded(serializedObject);
     

    } else {
      
        action = "updated";
        // Call callback for items updated
        cf.defaults.onItemUpdated(serializedObject);
  


    }

    products[$item.val()] = serializedObject;
    $.jStorage.set( PRODUCTS_KEY, products );


    updateCount();

    $form.trigger('cesta-feira-item-'+action);


    



  


  }

  function serializeObject($form){
    addrealtimeCart()
  
    var obj = {},
      arraySerial = $form.find('[data-cesta-feira-attribute]').serializeArray();

    $.each(arraySerial, function(){
      if (obj[this.name] !== undefined) {
        if (!obj[this.name].push) {
          obj[this.name] = [obj[this.name]];
        }
        obj[this.name].push(this.value || '');
      } else {
        obj[this.name] = this.value || '';
      }
    });

    return obj;

  }






  /**
   * Update counter items. Wrapper of the count is referenced by metadata 'data-cesta-feira-items-count'
   * @return void
   */
  function updateCount(){

    var $itemsCount = $wItemsCount.find( '.cesta-feira__num-items' );

    if( jQuery.isEmptyObject( getItems() ) ){

      $itemsCount.remove();

      return;
    }

    $.each($wItemsCount, function( index, value ){
      var $itemsCount = $(this).find('.cesta-feira__num-items');

      if(!$itemsCount.length){
        $itemsCount = $( "<span class=\"cesta-feira__num-items\" />" );

        $(this).append( $itemsCount );
      }

      $itemsCount.html( getNumItems() );

    });

  }

  /**
   * Get number of the items in basket
   * @return int
   */
  function getNumItems(){
    return Object.keys( $.jStorage.get( PRODUCTS_KEY ) ).length;
  }

  /**
   * Get items of the basket
   * @returns {*|Mixed}
   */
  function getItems(){
    return $.jStorage.get(PRODUCTS_KEY);
  }

  /**
   * Remove item in the basket
   * @param Item id
   */
  function removeItem(id){
    var items = getItems();

    var cf = $.CestaFeira();

    if (id in items){
      delete items[id]; // delete item
    } else {

      // Show some debug information if the variable is set and evaluates to true
      if ( cf.defaults.debug ) {
        console.info("[CestaFeira] - Item not found in the basket.");
      }

      return false;
    }

    $.jStorage.flush(); // Emptying the basket

    $.jStorage.set( PRODUCTS_KEY, items ); // Put new list of items in the basket.

    $document.trigger('cesta-feira-item-deleted');

    // Show some debug information if the variable is set and evaluates to true
    if ( cf.defaults.debug ) {
      console.info("[CestaFeira] - Item deleted!" );
    }

    updateCount();

    return true;
  }

  /**
   *  Clear basket
   *  @return void
   */
  function clearBasket(){

    var cf = $.CestaFeira();

    if($.jStorage.flush()){

      updateCount();

      if ( cf.defaults.debug ) {
        console.info("[CestaFeira] - Empty basket!");
      }

      $document.trigger('cesta-feira-clear-basket');

      return true;
    }

    if ( cf.defaults.debug ) {
      console.warn("[CestaFeira] - Problem when emptying basket!");
    }

    return false;
  }

  /**
   *  The Constructor
   */
  function CestaFeira(options) {

    /* Singleton (ensure unique instance) */
    if ( !instance ) {

      this.defaults = $.extend( {}, defaults, options );

      instance = this;

      this.init();
    }

    return instance;
  }

  $.extend( CestaFeira.prototype, {
    init: function() {

      var cf = $.CestaFeira();

      if ( cf.defaults.debug ) {
     
      }

      updateCount();

      $document.on('submit', 'form[data-cesta-feira-form]', submitForm);

      $document.on('click', '[data-cesta-feira-clear-basket]', function(e) {
        e.preventDefault();
        clearBasket();
      });

      $document.on('click', '[data-cesta-feira-delete-item]', function(e) {
        e.preventDefault();

        var productId = $(this).data('cesta-feira-delete-item');
        removeItem(productId);
      });

    },
    updateCount:    updateCount,
    getNumItems:    getNumItems,
    getItems:       getItems,
    removeItem:     function(itemId){ return removeItem(itemId); },
    clearBasket:    clearBasket
  } );

  $.extend( {
    CestaFeira: function( options ) {
      return ( new CestaFeira( options ) );
    }
  } );




  // cart js




  




    
  $(window).resize(function(){
    if ($(window).width()<980) {
     $('#removeatt').removeClass('shopping_bg');
    }
   });


   

  


  function initListaOrcamento() {
    var products = $.CestaFeira({
        debug: true
      }).getItems(),
      totalValueTemp = 0,
      $cartItems = $('.allcartview');

      





     

function updateTotalValue() {
    let subtotal = 0;
    let ship_cost = parseFloat($('#shipping_cost_display').text().replace('C$', '')) || 0;
    let tax      = parseFloat($('#tax_display').text().replace('C$', '')) || 0;

    // Sum item totals
    $('[data-item-total-value]').each(function () {
        let value = parseFloat($(this).data('item-total-value')) || 0;
        subtotal += value;
    });

    // Base total before any coupon
    let baseTotal = subtotal + ship_cost + tax;

    // Update displays (initial values without coupon)
    $('#subtotal-value').html(subtotal.toFixed(2));
    $('#subtotal_inp').val(subtotal.toFixed(2));
    $('#total-value').html("C$" + baseTotal.toFixed(2));   // or "$:" if you prefer
    $('#grand_total_inp').val(baseTotal.toFixed(2));
    $('#basket-total').html(baseTotal.toFixed(2));
    $('.total-cart').html(baseTotal.toFixed(2));

    // Clear previous discount display
    $("#show_discount").html("");
    $("#discount_amo").val("0");

    // Check if coupon exists → apply
    const couponCode = $('#coupon').val().trim();
    if (couponCode && $(".basket-product").length > 0) {
        CouponApplie(subtotal, ship_cost, tax);   // ← pass subtotal + fixed costs
    }
}

function CouponApplie(subtotal, ship_cost, tax) {
    const csrftoken = $("input[name='csrfmiddlewaretoken']").val();
    const coupon    = $('#coupon').val().trim();

    if (!coupon) return;

    $.ajax({
        url: "/check_coupon/",
        type: 'POST',
        data: {
            coupon: coupon,
            // Optionally send subtotal so backend can validate/re-calculate
            subtotal: subtotal.toFixed(2),
            csrfmiddlewaretoken: csrftoken
        },
        success: function (res) {
            if (res.resp === 'error') {
                $('#success_message_coupon')
                    .addClass('success_coupon_main_error')
                    .removeClass('success_coupon_main')
                    .removeClass('hide');

                $('#message_icon').addClass('bi-emoji-laughing');
                $('#message_cooupon').html(`<span style="font-weight: 600;">Sorry!</span> ${res.error}`);

                // Reset total display to pre-coupon state
                const baseTotal = subtotal + ship_cost + tax;
                $('#basket-total').text(baseTotal.toFixed(2));
                $('#grand_total_inp').val(baseTotal.toFixed(2));
                $("#show_discount").html("");
            } else {
                let discountedSubtotal = subtotal;
                let discountAmount = 0;

                if (res.data.formula === 'value') {
                    discountAmount = res.data.value;
                    discountedSubtotal = Math.max(0, subtotal - discountAmount);
                } 
                else if (res.data.formula === 'percentage') {
                    discountAmount = subtotal * (res.data.value / 100);
                    discountedSubtotal = subtotal - discountAmount;
                }

                // Final total = discounted items + shipping + tax
                const finalTotal = discountedSubtotal + ship_cost + tax;

                // Update displays
                $('#basket-total').text(finalTotal.toFixed(2));
                $('#grand_total_inp').val(finalTotal.toFixed(2));
                $("#show_discount").html(`(-) Discount <span id='dis_display'>-C$${discountAmount.toFixed(2)}</span>`);
                $("#discount_amo").val(discountAmount.toFixed(2));

                // Success message
                $('#success_message_coupon')
                    .addClass('success_coupon_main')
                    .removeClass('success_coupon_main_error')
                    .removeClass('hide');

                $('#message_cooupon').html(
                    `<span><span style="font-weight: 600;">Congratulations!</span> ` +
                    `Your Coupon is Applied</span> ` +
                    `<span class="coupon_remove"><i class="fa fa-times-circle"></i></span>`
                );
                $('#message_icon').addClass('bi-emoji-frown');   // ← maybe change to bi-emoji-smile ?
            }
        },
        error: function () {
            // Handle network error (optional)
            $('#message_cooupon').html("Coupon check failed. Please try again.");
        }
    });
}


  $('#message_cooupon').on('click' , '.coupon_remove' , function(){
    console.log('work')
    $('#coupon').val('')
    updateTotalValue()
    $("#show_discount").html(``)
    $('#message_cooupon').html(``);
    
    $('#success_message_coupon').addClass('hide');
  })
    

 $('.allcartviews , .side-panel-content').on('click', '.cart_item_del_btn', function(event) {
    let del_target = $(this).data('del_item');
    let cart_id = $(this).data('cart-id');
    let csrftoken = document.querySelector('meta[name="csrf-token"]').content; // safer meta-based token

    // animation first
    $(del_target).css({ 'transform': 'scale(0)' });

    setTimeout(function() {
        // 1️⃣ Delete from backend
        fetch(`/delete-cart-item/${cart_id}/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrftoken
            },
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                $(del_target).remove();
                updateTotalValue();

                // check if cart is empty after removal
                let items_len = $(".basket-product").length;

                if (items_len <= 0) {
                    showEmptyCartMessage();
                }
            } else {
                console.error("Backend delete failed:", data);
                alert("Failed to remove item from server!");
            }
        })
        .catch(err => console.error("Delete error:", err));
    }, 400);
});

function showEmptyCartMessage() {
    $("#show_discount").empty();
    $('#message_cooupon').empty();
    $('#coupon').val('');
    $('#success_message_coupon').addClass('hide');
    $('#empty-error').html(`
        <div class='alert alert-error alert-danger' role='alert'>
            Your Cart is empty, please add some items!
        </div>
        <img src='/static/shop/img/emp.png' style='max-width:100%;margin:auto;display:block;'>
    `);
    $(".primary-btn").css({
        background: "linear-gradient(262deg, #543b24a6 0%, #543b2494 100%)",
        cursor: "no-drop"
    }).attr("disabled", true);
    $("#basket-total, #subtotal-value").text('0');
}

$('#your-order').on('click', '.cart_item_del_btn', function(event) {
    let del_target = $(this).data('del_item');
    let cart_id = $(this).data('cart-id');
    let csrftoken = document.querySelector('meta[name="csrf-token"]').content; // same as main

    // animation first
    $(del_target).css({ 'transform': 'scale(0)' });

    setTimeout(function() {
        // delete from backend
        fetch(`/delete-cart-item/${cart_id}/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrftoken
            },
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                $(del_target).remove();
                updateTotalValue();

                let items_len = $(".basket-product").length;
                if (items_len <= 0) {
                    showEmptyCartMessageYourOrder();
                }
            } else {
                console.error("Backend delete failed:", data);
                alert("Failed to remove item from server!");
            }
        })
        .catch(err => console.error("Delete error:", err));
    }, 400);
});
    

         
   
$('#apply_submit_btn').click(function(){
  updateTotalValue()

})



    function mountLayout(index, data) {
      var totalValueTemp = parseFloat(data.unity_price) * parseInt(data.quantity);
      
      if (data.order_type === 'Customize'){
          var edit_link = ""
        }else{
          var edit_link = "<a class='' href='/product/"+ index +"'><i class='fa fa-edit'></i> Edit</a>"
        }
       var $layout ="<div class='basket-product ' id='cart_items_main_div"+index+"'>"+
        "<div class='item'>"+
        "<div class='product-image'>"+
        "<img class='product-frame' height='78px' src='"+data.item_type+"' alt='"+ data.product_name +"'>"+
        "</div>"+
        "<div class='product-details'>"+
        "<div class='product_name_del'>"+
          "<div class='product_vari'>"+
            "<h1 class='head'><strong><span class='item-quantity'>" + data.quantity +"</span> x " + data.product_brand +" </strong>"+ data.product_name.slice(0,30) +"..</h1>"+
            "<p><span class='"+ data.size +"'> Size :"+ data.size +" </span>  <span class='"+ data.color +"'> , Color :"+ data.color +" </span> </p>"+
            "<p>Product Code - "+ data.id +"</p>"+
          "</div>"+
          "<div class='remove'>"+
            "<a href='javascript:;' class='btn text-danger fa fa-trash cart_item_del_btn' data-del_item='#cart_items_main_div"+index+"' data-cesta-feira-delete-item='"+ index +"'><span class='sr-only'>Remove</span></a>"+         
          "</div>"+

        "</div>"+

        "<div class='price_and_qty_and_total'>"+
          "<div class='price'>"+currency+""+ data.unity_price +"</div>"+
          "<div class='item_quantity'>"+
          "<div class='item-qty'>Qty. " + data.quantity +"</div>"+
          ""+edit_link+""+
          "</div>"+
          "<div class='subtotal' data-item-total-value='"+totalValueTemp+"'>"+currency+""+parseFloat(totalValueTemp)+"</div>"+
        "</div>"+

        "</div>"+
        "</div>"+
     
        "</div>";


       


         var $lilist = "<li class='checkout_list' id='cart_items_main_div"+index+"'>"+
        "<a href='javascript:;' class='remove bg-danger text-white cart_item_del_btn' data-del_item='#cart_items_main_div"+index+"' data-cesta-feira-delete-item='" + index + "'  title='Remove this item'><i class='fa fa-remove'></i></a>"+
        "<a class='cart-img' href='/product/" + index + "'><img src='" + data.item_type + "' alt='" + data.product_name + "'></a>"+
        "<h4><a href='/product/" + index + "'>" + data.product_name.slice(0, 15) + "...</a></h4>"+
        "<p class='quantity' data-item-total-value='" + totalValueTemp + "'>"+currency+"." + data.unity_price + "x" + data.quantity + " = "+currency+"." + parseFloat(totalValueTemp) + "</p>"+
        
        "</li>";



        var show_btn =  `<div class='side_action_btn_parent'>
        <div class="cart_link_in_side">
        <a href='/cart/'>View Cart</a>
        </div>

        <div class="cart_link_in_side checkbtn_color">
            <a href='/checkout/'>
            checkout
            </a>
            </div>
        </div>`


        $(".side-panel-action-btn").html(show_btn)

        
        $cartItems.append($layout);
        $("#your-order").append($layout);
        $(".side-panel-content").append($layout);


      

     
      }
      
      
    
    

   

      


      

    
      
      
      
    
      
      $.each(products,function (index, value) {
        mountLayout(index, value);
      var jsonstr = JSON.stringify(products)
      var phoneName = JSON.parse(jsonstr);
      var finaljsonstrval = JSON.stringify(phoneName[index]);
      var finaljsonparseval = JSON.parse(finaljsonstrval);
      
     
      $('.addcheckoutform').append("<input type='hidden' id='id' name='id[]' readonly value='"+ finaljsonparseval['id'] +"'>")

      $('.addcheckoutform').append("<input type='hidden' id='mockup_id' name='mockup_id[]' readonly value='"+ finaljsonparseval['mockup_id'] +"'>")

      $('.addcheckoutform').append("<input type='hidden' id='product_name' name='product_name[]' readonly value='"+ finaljsonparseval['product_name'] +"'>")
      $('.addcheckoutform').append("<input type='hidden' id='product_brand' name='product_brand[]' readonly value='"+ finaljsonparseval['product_brand'] +"'>")
      $('.addcheckoutform').append("<input type='hidden' id='quantity' name='quantity[]' readonly value='"+ finaljsonparseval['quantity'] +"'>")
      $('.addcheckoutform').append("<input type='hidden' id='size' name='size[]' readonly value='"+ finaljsonparseval['size'] +"'>")
      $('.addcheckoutform').append("<input type='hidden' id='color' name='color[]' readonly value='"+ finaljsonparseval['color'] +"'>")
      $('.addcheckoutform').append("<input type='hidden' id='item_type' name='item_type[]' readonly value='"+ finaljsonparseval['item_type'] +"'>")
      $('.addcheckoutform').append("<input type='hidden' id='order_status' name='order_status[]' readonly value='"+ finaljsonparseval['order_status'] +"'>")
      

      $('.addcheckoutform').append("<input type='hidden' id='fornt_design_id' name='fornt_design_id[]' readonly value='"+ finaljsonparseval['fornt_design_id'] +"'>")
      $('.addcheckoutform').append("<input type='hidden' id='fornt_design_price' name='fornt_design_price[]' readonly value='"+ finaljsonparseval['fornt_design_price'] +"'>")

      $('.addcheckoutform').append("<input type='hidden' id='back_design_id' name='back_design_id[]' readonly value='"+ finaljsonparseval['back_design_id'] +"'>")
      $('.addcheckoutform').append("<input type='hidden' id='back_design_price' name='back_design_price[]' readonly value='"+ finaljsonparseval['back_design_price'] +"'>")
      $('.addcheckoutform').append("<input type='hidden' id='text_print_front' name='text_print_front[]' readonly value='"+ finaljsonparseval['text_print_front'] +"'>")
      $('.addcheckoutform').append("<input type='hidden' id='text_print_front_price' name='text_print_front_price[]' readonly value='"+ finaljsonparseval['text_print_front_price'] +"'>")

      $('.addcheckoutform').append("<input type='hidden' id='text_print_back' name='text_print_back[]' readonly value='"+ finaljsonparseval['text_print_back'] +"'>")

      $('.addcheckoutform').append("<input type='hidden' id='text_print_back_price' name='text_print_back_price[]' readonly value='"+ finaljsonparseval['text_print_back_price'] +"'>")

      $('.addcheckoutform').append("<input type='hidden' id='order_type' name='order_type[]' readonly value='"+ finaljsonparseval['order_type'] +"'>")


      });
      
      
      updateTotalValue();
      
 

      $(document).on('click', 'a[data-cesta-feira-delete-item]', function(e) {
        e.preventDefault();
        
        var productId = $(this).data('cesta-feira-delete-item');
        
        if($(document).on('cesta-feira-item-deleted')){
          $('#product-'+productId).fadeOut(500, function() {
            $(this).remove();
            updateTotalValue();
          });
        }
      });
      
      $(document).on('cesta-feira-clear-basket', function (e) {
        $('#cart-items tr').each(function (index, value) {
          $(value).fadeOut(500, function() {
            $(this).remove();
            updateTotalValue();
          });
        });
      });
      
    }


    

    
    $(document).ready(function () {
      
      initListaOrcamento();

      
      
    });
    

   
    
    
    //  <script type="text/javascript">
    
    //   var _gaq = _gaq || [];
    //   _gaq.push(['_setAccount', 'UA-36251023-1']);
    //   _gaq.push(['_setDomainName', 'jqueryscript.net']);
    //   _gaq.push(['_trackPageview']);
    
    //   (function() {
      //     var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
      //     ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
      //     var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
      //   })();
      
// </script>

// $(document).bind("contextmenu",function(e) {
//   e.preventDefault();
//  });

//  $(document).keydown(function(e){
//   if(e.which === 123){
//      return false;
//   }
// });


})(jQuery, document); // Fully reference jQuery after this point.





