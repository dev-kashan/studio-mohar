var script= document.createElement('script');
script.type='text/javascript';
script.src="https://cdn.tiny.cloud/1/wbjjx25h2x7u6ajwsnknzp0w0i8edo123lj8acvxkokvc5z8/tinymce/5/tinymce.min.js";
document.head.appendChild(script);
// var alert_remove = document.getElementsByClassName('tox-notifications-container');
// alert_remove.setAttribute("id","para-1");
// console.log(alert_remove);

script.onload=function(){
  // alert_remove.style.display = 'none';
tinymce.init({
    selector: "#id_product_item",
    selector: "#id_desc",
    height:656,
    element_format : 'html',
    plugins: [
      'advlist', 'autolink', 'link', 'image', 'lists', 'charmap', 'preview', 'anchor', 'pagebreak',
      'searchreplace', 'wordcount', 'visualblocks', 'visualchars', 'code', 'fullscreen', 'insertdatetime',
      'media', 'table', 'emoticons', 'template', 'help'
    ],
    toolbar: 'undo redo | styles | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link image | print preview media | forecolor backcolor emoticons',
    menu: {
      favs: { title: 'My Favorites', items: 'code visualaid | searchreplace | emoticons' }
    },
    menubar: 'favs file edit view insert format tools table help',
      content_css: 'css/content.css'
    });

   

tinymce.init({
  selector: "#id_article",
  height:656,
  element_format : 'html',
  plugins: [
      'advlist autolink link image lists charmap print preview hr anchor pagebreak',
      'searchreplace wordcount visualblocks visualchars code fullscreen insertdatetime media nonbreaking',
      'table emoticons template paste help'
    ],
    toolbar: 'undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | ' +
      'bullist numlist outdent indent | link image | print preview media fullpage | ' +
      'forecolor backcolor emoticons | help',
    menu: {
      favs: {title: 'My Favorites', items: 'code visualaid | searchreplace | emoticons'}
    },
    menubar: 'favs file edit view insert format tools table help',
    content_css: 'css/content.css'
  });


}