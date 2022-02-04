$(function () {
    $(document).ready(function () {
        $('.textboard-container').removeClass('no-js');
        
        $("#create-thread-link").on("click", function () {
            this.style.display = "none";
            $("#create-thread-panel")[0].removeAttribute("hidden");
        });

        $(".post-reply").on("click", function () {
            $("#reply-panel")[0].style.display = "block";
            $("#reply-content")[0].value += ">>>"+this.dataset.postid;
        });

        $("#close-reply-panel-button").on("click", function () {
            $("#reply-panel")[0].style.display = "none";
            $("#reply-content").val('');
        });
    });
});