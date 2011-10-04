function DisplayAdvSearch(search_a) {
  $('#adv-searchbox').attr('style','display:inline');
  $('#basic-searchbox').attr('style','display:none');
  $(search_a).text('Basic Search');
  
}


function DisplayBasicSearch(search_a) {
  $('#adv-searchbox').attr('style','display:none');
  $('#basic-searchbox').attr('style','display:inline');
  $(search_a).text('Advanced Search');
}

function DisplayFacet(facet_a) {
 // Cycle through and close other facets

 var h5 = $(facet_a).children()[0];
 var ul = $(facet_a).next();
 if($(h5).attr('class') == 'closed') {
   $(h5).attr('class','');
   $(ul).attr('class','open');
 } else {
   $(h5).attr('class','closed');
   $(ul).attr('class','closed');
 }
 return false;
}

function DisplayItems(more_dd) {
  $("dd").attr('style','');
  $(more_dd).remove();
}

function DisplayRows(row_count_select) {
 var new_row_count = $(row_count_select).attr('value');
 $('#solr_rows').attr('value',new_row_count);
 document.forms['catalog_search'].submit();

}

function DisplaySearch(search_a) {
   var label = $(search_a).text();
   if(label == 'Basic Search') {
      DisplayBasicSearch(search_a);
   }
   if(label == 'Advanced Search') {
      DisplayAdvSearch(search_a);
   }

}

function FilterByFacet(facet,value) {
 $('#catalog_search').append('<input type="hidden" name="fq" value="' + facet + ':' + value + '">');
 document.forms['catalog_search'].submit();

}

function handleResultPaginateClick(new_page_index,pagination_container) {
  var data = 'func=search&search-type=' + $("input[name~='search-type']").val();
  data += '&page_index=' + new_page_index;
  data += '&rows=' + $("#solr_rows").val();
  $("input[name~='q']").each(
    function(i,v) {
     data += '&q=' + $(v).val();
  });
  $("input[name~='fq']").each(
    function(i,v) {
      data += '&fq=' + $(v).val();
  });
  $.ajax({
      type: 'get',
       url: '/catalog/rpc',
      data: data,
   success: function(responseText) {
      $('.results-list').remove();
      $('#main-content').attr('innerHTML',responseText);
    }
   });

  return false;
}


function ProcessSearchQuery() {
  var new_q = $('#book-search').value();
  new_q += set_fieldname("field1");
  new_q += set_fieldname("field2");
  new_q += set_fieldname("field3");
  $('#book-search').attr('value',new_q);
  //document.forms['catalog_search'].submit();
}

function set_fieldname(field_stem) {
  var search_type = "input[name~='" + field_stem + "_type']";
  var search_phrase = "input[name~='" + field_stem + "_phrase']";
  var search_operator = "input[name~='" + field_stem + "_operator']";

  var output = ' ';
  if ($(search_type).value()) {
    output += $(search_type).value() + ':' + $(search_phrase).value();
  } else {
    output += $(search_phrase).value();
  }
  if (output.length > 2) {
    output += ' ' + $(search_operator).value();
  }
 return output;
}
