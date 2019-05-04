(function ($) {
  'use strict';

  $(function () {
    let isHashtagGiven = false;
    let isStartDateGiven = false;
    let isEndDateGiven = false;
    const $submitButton = $("#submitter"); 
    
    /*returns an array with all the chips tags*/
    const getChipsData = () => {
      var chipInstance = M.Chips.getInstance($(".chips"));
      var chipsArray = chipInstance.chipsData;
      var chipsDataArray = [];
      for (var i = 0; i < chipsArray.length; i++){
        var chip = chipsArray[i].tag;
        chipsDataArray.push(chip);
      }
      return chipsDataArray;
    };

    const enableSubmit = () => {
      $submitButton.removeClass("disabled");
    };

    const disableSubmit = () => {
      $submitButton.addClass("disabled");
    };

    const getDate = $el => $el.context.M_Datepicker.date;

    const checkForInput = () => isHashtagGiven && isEndDateGiven && isStartDateGiven;

    const dateComparator = (date) => {
      if(date > new Date()) return new Date();
      else return date;
    }

    const checkForChips = e => {
      if ($(".chip").toArray().length > 0) {
        isHashtagGiven = true;
        if (checkForInput()) enableSubmit();
        document.getElementById('hidden-tags').value = JSON.stringify(getChipsData());
      }
      else {
        isHashtagGiven = false;
        disableSubmit();
      }
    };

    $('#start-date').on('change', function (e) {
      isStartDateGiven = true;
      if (checkForInput()) enableSubmit();

      $('#end-date').datepicker({
        minDate: getDate($(this)),
        maxDate: new Date(),
        format: 'yyyy-mm-dd'
      });
    });

    $('#end-date').on('change', function (e) {
      isEndDateGiven = true;
      if (checkForInput()) enableSubmit();

      $('#start-date').datepicker({
        maxDate: dateComparator(getDate($(this))),
        format: 'yyyy-mm-dd'
      });
    });

    $('.sidenav').sidenav();
    $('.parallax').parallax();
    $('.chips').chips({
      placeholder: 'Write a hashtag, then press enter',
      secondaryPlaceholder: '+Hashtag',
      onChipAdd: checkForChips,
      onChipDelete: checkForChips
    });

    $(document).ready(function () {
      $('#start-date').datepicker({
        maxDate: new Date(),
        format: 'yyyy-mm-dd',
        defaultDate: new Date(2017,10,15),
        setDefaultDate: true,
      });
      $('#end-date').datepicker({
        maxDate: new Date(),
        format: 'yyyy-mm-dd',
        defaultDate: new Date(2017,10,16),
        setDefaultDate: true,
      });
    });

  }); // end of document ready
})(jQuery); // end of jQuery name space
