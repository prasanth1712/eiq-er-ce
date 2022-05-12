// place any jQuery/helper plugins in here, instead of separate, slower script files.


$(function() {
    var csrftoken = $('meta[name=csrf-token]').attr('content')

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    })

    $(function(){
        var hash = window.location.hash;
        hash && $('ul.nav a[href="' + hash + '"]').tab('show');

        $('.nav-tabs a').click(function (e) {
            $(this).tab('show');
            window.location.hash = this.hash;
            $(window).scrollTop(0);
        });

    });



    $('.glyphicon-trash').on('click', function(event) {

        var tr = $(this).parents('tr');

        $.ajax({
            url: $(this).data('uri'),
            contentType: "application/json",
            type: "DELETE"
        }).done(function (data, textStatus, jqXHR) {
            $(tr).remove();
            console.log(jqXHR.status);
        });

    })



    $('.activate-node').on('click', function(event) {
         if ($(this).data('uri') == null || $(this).data('uri') == ''){
            return;}

        var el = $(this);

        $.post($(this).data('uri'), {
            is_active: $(this).hasClass('glyphicon-unchecked') || null
        }).done(function (data, textStatus, jqXHR) {
            $(el).toggleClass('glyphicon-check glyphicon-unchecked');
        });

    })

    // $('body').scrollspy({
    //     target: '.bs-docs-sidebar',
    //     offset: 70
    // })

//    $('#sidebar').affix({
//        offset: {
//            top: 0
//        }
//    })

    // --------------------------------------------------------------------------------


})





function  init_querybuilder(exist_query) {
    // console.log(typeof(exist_query));

   var $queryBuilder = $('#query-builder');

    if ($queryBuilder.length) {

        var QueryBuilder = $.fn.queryBuilder.constructor;

        var SUPPORTED_OPERATOR_NAMES = ['equal', 'not_equal', 'begins_with', 'not_begins_with', 'contains', 'not_contains', 'ends_with', 'not_ends_with', 'is_empty', 'is_not_empty', 'less', 'less_or_equal', 'greater', 'greater_or_equal',];
        var SUPPORTED_OPERATORS = SUPPORTED_OPERATOR_NAMES.map(function (operator) {
            return QueryBuilder.OPERATORS[operator];
        });
        var COLUMN_OPERATORS = SUPPORTED_OPERATOR_NAMES.map(function (operator) {
            return {
                type: 'column_' + operator,
                nb_inputs: QueryBuilder.OPERATORS[operator].nb_inputs + 1,
                multiple: true,
                apply_to: ['string'],
            };
        });
        var SUPPORTED_COLUMN_OPERATORS = SUPPORTED_OPERATOR_NAMES.map(function (operator) {
            return 'column_' + operator;
        });
        var CUSTOM_LANG = {};
        SUPPORTED_OPERATOR_NAMES.forEach(function (op) {
            CUSTOM_LANG['column_' + op] = QueryBuilder.regional.en.operators[op];
        });
        Array.prototype.push.apply(SUPPORTED_OPERATOR_NAMES, ['matches_regex', 'not_matches_regex', 'matches_wildcard', 'not_matches_wildcard', 'matches_phish_tank']);
        Array.prototype.push.apply(SUPPORTED_OPERATORS, [{
            type: 'matches_regex',
            nb_inputs: 1,
            multiple: true,
            apply_to: ['string'],
        }, {type: 'not_matches_regex', nb_inputs: 1, multiple: true, apply_to: ['string'],}, {
            type: 'matches_wildcard',
            nb_inputs: 1,
            multiple: true,
            apply_to: ['string'],
        }, {
            type: 'not_matches_wildcard',
            nb_inputs: 1,
            multiple: true,
            apply_to: ['string'],
        }, {type: 'matches_phish_tank', nb_inputs: 1, multiple: true, apply_to: ['string'],},]);
        CUSTOM_LANG['matches_regex'] = 'matches regex';
        CUSTOM_LANG['not_matches_regex'] = "doesn't match regex";
        CUSTOM_LANG['matches_wildcard'] = "matches wildcard";
        CUSTOM_LANG['not_matches_wildcard'] = "doesn't match wildcard";
        CUSTOM_LANG['matches_phish_tank'] = "matches phishtank intel";
        Array.prototype.push.apply(SUPPORTED_COLUMN_OPERATORS, ['column_matches_regex', 'column_not_matches_regex', 'column_matches_wildcard', 'column_not_matches_wildcard', 'column_matches_phish_tank']);
        Array.prototype.push.apply(COLUMN_OPERATORS, [{
            type: 'column_matches_regex',
            nb_inputs: 2,
            multiple: true,
            apply_to: ['string'],
        }, {
            type: 'column_not_matches_regex',
            nb_inputs: 2,
            multiple: true,
            apply_to: ['string'],
        }, {
            type: 'column_matches_wildcard',
            nb_inputs: 2,
            multiple: true,
            apply_to: ['string'],
        }, {
            type: 'column_not_matches_wildcard',
            nb_inputs: 2,
            multiple: true,
            apply_to: ['string'],
        }, {type: 'column_matches_phish_tank', nb_inputs: 2, multiple: true, apply_to: ['string'],},]);
        CUSTOM_LANG['column_matches_phish_tank'] = 'matches phishtank intel';
        CUSTOM_LANG['column_matches_regex'] = "match regex";
        CUSTOM_LANG['column_not_matches_regex'] = "doesn't match regex";
        CUSTOM_LANG['column_matches_wildcard'] = "matches wildcard";
        CUSTOM_LANG['column_not_matches_wildcard'] = "doesn't match wildcard";
        // var existingRules;
            
        // try {
        //     var v = $('#rules-hidden').val();
        //     console.log($('#rules-hidden').val())
        //     if ($('#rules-hidden').val() != '') {
        //         console.log(v);
        //         existingRules = $('#rules-hidden').val()
        //         // existingRules =  {'rules': [{'id': 'column', 'type': 'string', 'field': 'column', 'input': 'text', 'value': ['tester1', '123456'], 'operator': 'column_equal'}], 'condition': 'AND'};
                
        //         console.log(existingRules);
        //     }
        // } catch (e) {
        //     console.log(e);
        // }
        var existingRules = exist_query;
        // console.log(JSON.parse(exist_query));
        $queryBuilder.queryBuilder({
          plugins: {
          'bt-selectpicker': {
              // liveSearch: true,
              // liveSearchPlaceholder: 'Search here...',
              // html: true,
              width: '200px'

          }
        },
            filters: [{
                id: 'query_name',
                type: 'string',
                label: 'Query Name',
                operators: SUPPORTED_OPERATOR_NAMES,
            }, {
                id: 'action',
                type: 'string',
                label: 'Action',
                operators: SUPPORTED_OPERATOR_NAMES,
            }, {
                id: 'host_identifier',
                type: 'string',
                label: 'Host Identifier',
                operators: SUPPORTED_OPERATOR_NAMES,
            }, {
                id: 'timestamp',
                type: 'integer',
                label: 'Timestamp',
                operators: SUPPORTED_OPERATOR_NAMES,
            }, {
                id: 'column',
                type: 'string',
                label: 'Column',
                operators: SUPPORTED_COLUMN_OPERATORS,
                placeholder: 'value',
            },],
            operators: SUPPORTED_OPERATORS.concat(COLUMN_OPERATORS),
            lang: {operators: CUSTOM_LANG,},
            rules: existingRules,
        });
        $queryBuilder.on('getRuleInput.queryBuilder.filter', function (evt, rule, name) {
            if (rule.operator.type.match(/^column_/) && name.match(/value_0$/)) {
                var el = $(evt.value);
                $(el).attr('placeholder', 'column name');
                ;evt.value = el[0].outerHTML;
            }
        });
        $('#submit-button').on('click', function (e) {
            var $builder = $queryBuilder;
            
            if (!$builder) {
                return true;
            }
            debugger
            if (!$builder.queryBuilder('validate')) {
                e.preventDefault();
                $('#rules-hidden').val('');
                return false;
            }
            else{
                var rules = JSON.stringify($builder.queryBuilder('getRules'));
                console.log(rules);
                $('#rules-hidden').val(rules);
                return true;
            }
        });
    }
    // var query= {'rules': [{'id': 'column', 'type': 'string', 'field': 'column', 'input': 'text', 'value': ['wqewqsadsad', '1213'], 'operator': 'column_equal'}], 'valid': True, 'condition': 'AND'};
    // $queryBuilder.queryBuilder('setRules', query);

}
