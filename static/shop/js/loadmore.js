$(document).ready(function(){

$("#load-more").on('click' , function(){
    var _currentproduct = $(".current-product").length;
    var _limit = $(this).attr('data-limil');
    var _total = $(this).attr('data-total');
    // console.log(currentproduct , _limit , _total)
    // Run Ajax
    $.ajax({
        url:'/load-more',
        data:{
            filterlimit:_limit,
            currentproduct:_currentproduct
            
        },
        dataType:'json',
        beforeSend:function(){
            $("#load-more").attr('disabled' , true);
            $(".load-more-icon").addClass("fa-spin");
        },
        success:function(res){
            $("#addloadproduct").append(res.data);
            $("#load-more").attr('disabled' , false);
            $(".load-more-icon").removeClass("fa-spin");
            var totalshowing = $(".current-product").length;
            if(totalshowing == _total){
                $("#load-more").remove()
            }
        }
    });

});


});

