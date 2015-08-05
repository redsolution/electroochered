// place any jQuery/helper plugins in here, instead of separate, slower script files.

//usage: log('inside coolFunc', this, arguments);
//paulirish.com/2009/log-a-lightweight-wrapper-for-consolelog/
window.log = function() {
    log.history = log.history || [];   // store logs to an array for reference
    log.history.push(arguments);
    if(this.console) {
        arguments.callee = arguments.callee.caller;
        var newarr = [].slice.call(arguments);
        (typeof console.log === 'object' ? log.apply.call(console.log, console, newarr) : console.log.apply(console, newarr));
    }
};

// make it safe to use console.log always
(function(b){function c(){}for(var d="assert,count,debug,dir,dirxml,error,exception,group,groupCollapsed,groupEnd,info,log,timeStamp,profile,profileEnd,time,timeEnd,trace,warn".split(","),a;a=d.pop();){b[a]=b[a]||c}})((function(){try
{console.log();return window.console;}catch(err){return window.console={};}})());

// parseUri 1.2.2
// (c) Steven Levithan <stevenlevithan.com>
// MIT License

function parseUri (str) {
	var	o   = parseUri.options,
		m   = o.parser[o.strictMode ? "strict" : "loose"].exec(str),
		uri = {},
		i   = 14;

	while (i--) uri[o.key[i]] = m[i] || "";

	uri[o.q.name] = {};
	uri[o.key[12]].replace(o.q.parser, function ($0, $1, $2) {
		if ($1) uri[o.q.name][$1] = $2;
	});

	return uri;
};

parseUri.options = {
	strictMode: false,
	key: ["source","protocol","authority","userInfo","user","password","host","port","relative","path","directory","file","query","anchor"],
	q: {
		name:   "queryKey",
		parser: /(?:^|&)([^&=]*)=?([^&]*)/g
	},
	parser: {
		strict: /^(?:([^:\/?#]+):)?(?:\/\/((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?))?((((?:[^?#\/]*\/)*)([^?#]*))(?:\?([^#]*))?(?:#(.*))?)/,
		loose:  /^(?:(?![^:@]+:[^:@\/]*@)([^:\/?#.]+):)?(?:\/\/)?((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?)(((\/(?:[^?#](?![^?#\/]*\.[^?#\/.]+(?:[?#]|$)))*\/?)?([^?#\/]*))(?:\?([^#]*))?(?:#(.*))?)/
	}
};

;function cloneMore(selector, type) {
    var newElement = $(selector).clone(true);
    var total = $('#id_' + type + '-TOTAL_FORMS').val();
    newElement.find(':input').each(function() {
        var name = $(this).attr('name').replace('-' + (total-1) + '-','-' + total + '-');
        var id = 'id_' + name;
        $(this).attr({'name': name, 'id': id}).val('').removeAttr('checked');
    });
    newElement.find('label').each(function() {
        var newFor = $(this).attr('for').replace('-' + (total-1) + '-','-' + total + '-');
        $(this).attr('for', newFor);
    });
    total++;
    $('#id_' + type + '-TOTAL_FORMS').val(total);
    newElement.hide();
    $(selector).after(newElement);
    newElement.show(400);
};

function bind_new_regexp($input, regexp) {
    var pattern = new RegExp(regexp);
    $input.off('keyup').on('keyup', function() {
        var input_value = $input.val();
        if (input_value) {
            if (pattern.test(input_value)) {
                $input.parents('div.field').removeClass('error');
            } else {
                $input.parents('div.field').addClass('error');
            }
        } else {
            $input.parents('div.field').removeClass('error');
        }
    });
}

function change_document_hint($input, help_text) {
    $input = $input.parent()
    if (help_text) {
        help_text = "Формат документа: " + help_text;
    } else {
        help_text = '&nbsp;';
    }

    if ($input.siblings('p.hint').length) {
        $input.siblings('p.hint').html(help_text);
    } else {
        var help_element = $('<p class="hint">').html(help_text);
        $input.after(help_element);
    }
}

(function ($) {

    /**
     * Плагин для изменения поля ввода номера документа
     *
     * Валидирует содержимое поля ввода для номера документа в соответствии с выбранным шаблоном.
     * Использовать так:
     *
     * поле выбора документа            селектор поля ввода номера
     *        V                                     V
     * $('#id_template').regexpValidate('#id_document_number');
     */
    $.fn.regexpValidate = function (input_selector) {
        var $docnumber_input = $(input_selector);
        return this.each(function() {
            var $this = $(this);
            $this.on('change', function() {
                if ($(this).val()) {
                    var doc_template = DOCUMENT_TEMPLATES[$(this).val()];
                    change_document_hint($docnumber_input, doc_template['help_text']);
                    bind_new_regexp($docnumber_input, doc_template['regexp']);
                } else {
                    change_document_hint($docnumber_input, '');
                }
            }).trigger('change');
        });
    };

    // Валидирует содержимое полей для ввода СНИЛС
    $.fn.snilsValidate = function () {
        $(this).on('keyup', function() {
            var input = $(this).val();
            if (input) {
                var pattern = new RegExp('^[0-9]{3}-[0-9]{3}-[0-9]{3} [0-9]{2}$');
                if (pattern.test(input)) {
                    $(this).parents('div.field').removeClass('error');
                } else {
                    $(this).parents('div.field').addClass('error');
                }
            } else {
                $(this).parents('div.field').removeClass('error');
            }
        });
    };

    // плагин изменяет внешний вид формы документов заявителя
    // в зависимости от выбранного типа документа
    $.fn.personalDocumentFormHandler = function () {
        change_personal_document_form($(this));

        $(this).on('change', function() {
            change_personal_document_form($(this));
        });
    };

    function change_personal_document_form($choice_selector) {
        var doc_type = $choice_selector.val();
        var $doc_form = $choice_selector.parents('div.personal-document-area');
        var $doc_fields = $doc_form.find('div.field');
        var $doc_name_field = $doc_fields.find('#id_doc_name').parents('div.field');
        var $doc_series_field = $doc_fields.find('#id_series').parents('div.field');
        var $doc_number_field = $doc_fields.find('#id_number').parents('div.field');
        var $doc_issued_by_field = $doc_fields.find('#id_issued_by').parents('div.field');
        var format_error_regexp = new RegExp('^.*неверный формат.*$');
        if (doc_type == 1) { // тип документа "Иное"
            $doc_name_field.removeClass('hidden');
            if (!$doc_name_field.find('input').val()) {
                $doc_name_field.find('a').hide();
                $doc_name_field.find('label.value').hide();
                $doc_name_field.find('input').show().focus();
            }
            $doc_name_field.find('label span.hint').hide();
            $doc_series_field.find('label span.hint').show();
            $doc_series_field.removeClass('error');
            $doc_series_field.find('label span.errors').text('');
            $doc_issued_by_field.find('label span.hint').show();
            $doc_issued_by_field.removeClass('error');
            $doc_issued_by_field.find('label span.errors').text('');
            if (format_error_regexp.test($doc_number_field.find('label span.errors').text())) {
                $doc_number_field.removeClass('error');
                $doc_number_field.find('label span.errors').text('');
            }
        } else {
            $doc_name_field.find('input').val('');
            $doc_name_field.addClass('hidden');
            $doc_name_field.removeClass('error');
            $doc_name_field.find('label.field-label span').html('');
            $doc_name_field.find('label span.hint').show();
            $doc_series_field.find('label span.hint').hide();
            $doc_issued_by_field.find('label span.hint').hide();
        }
        // валидация содержимого полей "серия" и "номер" для типа документа "Паспорт"
        if (doc_type == 2) {
            $doc_series_field.find('p.hint').html('Формат: 1234');
            bind_new_regexp($doc_series_field.find('input'), '^[0-9]{4}$');
            $doc_number_field.find('p.hint').html('Формат: 123456');
            bind_new_regexp($doc_number_field.find('input'), '^[0-9]{6}$');
        } else {
            $doc_series_field.find('p.hint').html('');
            $doc_series_field.find('input').off('keyup');
            $doc_number_field.find('p.hint').html('');
            $doc_number_field.find('input').off('keyup');
        }
    }

    // плагин влияет на отображение текстового поля "степень родства заявителя"
    $.fn.kinshipFieldHandler = function () {
        change_kinship_field_view($(this));

        $(this).on('change', function() {
            change_kinship_field_view($(this));
        });
    };

    function change_kinship_field_view($choice_selector) {
        var kinship_type = $choice_selector.val();
        var $kinship_choice_field = $choice_selector.parents('div.field');
        var $kinship_text_field = $('#id_kinship').parents('div.field');
        if (kinship_type == '0') {
            $kinship_text_field.removeClass('hidden');
            $kinship_text_field.find('label span.hint').hide();
            if (!$kinship_text_field.find('input').val()) {
                $kinship_text_field.find('a').hide();
                $kinship_text_field.find('label.value').hide();
                $kinship_text_field.find('input').show().focus();
            }
        } else if (kinship_type == '') {
            $kinship_text_field.addClass('hidden');
            $kinship_text_field.find('input').val('');
            $kinship_text_field.removeClass('error');
            $kinship_text_field.find('label.field-label span').html('');
        } else {
            $kinship_text_field.find('input').val('');
            $kinship_text_field.addClass('hidden');
            $kinship_text_field.removeClass('error');
            $kinship_text_field.find('label.field-label span').html('');
        }
    }

})(jQuery);


(function($){
    $.fn.serializeObject = function() {
        var o = {};
        var a = this.serializeArray();
        $.each(a, function() {
            if (this.value) {
                if (o[this.name] !== undefined) {
                    if (!o[this.name].push) {
                        o[this.name] = [o[this.name]];
                    }
                    o[this.name].push(this.value || '');
                } else {
                    o[this.name] = this.value || '';
                }
            }
        });
        return o;
    };
})(jQuery);


/**
 * jQuery Formset 1.2
 * @author Stanislaus Madueke (stan DOT madueke AT gmail DOT com)
 * @requires jQuery 1.2.6 or later
 *
 * Copyright (c) 2009, Stanislaus Madueke
 * All rights reserved.
 *
 * Licensed under the New BSD License
 * See: http://www.opensource.org/licenses/bsd-license.php
 */
// внес изменение: при добавлении формы значения полей остаются прежними
;(function($) {
    $.fn.formset = function(opts) {
        var options = $.extend({}, $.fn.formset.defaults, opts),
            flatExtraClasses = options.extraClasses.join(' '),
            $$ = $(this),

            applyExtraClasses = function(row, ndx) {
                if (options.extraClasses) {
                    row.removeClass(flatExtraClasses);
                    row.addClass(options.extraClasses[ndx % options.extraClasses.length]);
                }
            },

            updateElementIndex = function(elem, prefix, ndx) {
                var idRegex = new RegExp('(' + prefix + '-\\d+-)|(^)'),
                    replacement = prefix + '-' + ndx + '-';
                if (elem.attr("for")) elem.attr("for", elem.attr("for").replace(idRegex, replacement));
                if (elem.attr('id')) elem.attr('id', elem.attr('id').replace(idRegex, replacement));
                if (elem.attr('name')) elem.attr('name', elem.attr('name').replace(idRegex, replacement));
            },

            hasChildElements = function(row) {
                return row.find('input,select,textarea,label').length > 0;
            },

            insertDeleteLink = function(row) {
                if (row.is('TR')) {
                    // If the forms are laid out in table rows, insert
                    // the remove button into the last table cell:
                    row.children(':last').append('<a class="' + options.deleteCssClass +'" href="javascript:void(0)">' + options.deleteText + '</a>');
                } else if (row.is('UL') || row.is('OL')) {
                    // If they're laid out as an ordered/unordered list,
                    // insert an <li> after the last list item:
                    row.append('<li><a class="' + options.deleteCssClass + '" href="javascript:void(0)">' + options.deleteText +'</a></li>');
                } else {
                    // Otherwise, just insert the remove button as the
                    // last child element of the form's container:
                    row.append('<a class="' + options.deleteCssClass + '" href="javascript:void(0)">' + options.deleteText +'</a>');
                }
                row.find('a.' + options.deleteCssClass).click(function() {
                    var row = $(this).parents('.' + options.formCssClass),
                        del = row.find('input:hidden[id $= "-DELETE"]');
                    if (del.length) {
                        // We're dealing with an inline formset; rather than remove
                        // this form from the DOM, we'll mark it as deleted and hide
                        // it, then let Django handle the deleting:
                        del.val('on');
                        row.hide();
                    } else {
                        row.remove();
                        // Update the TOTAL_FORMS form count.
                        // Also update names and IDs for all remaining form controls so they remain in sequence:
                        var forms = $('.' + options.formCssClass).not('.formset-custom-template');
                        $('#id_' + options.prefix + '-TOTAL_FORMS').val(forms.length);
                        for (var i=0, formCount=forms.length; i<formCount; i++) {
                            applyExtraClasses(forms.eq(i), i);
                            forms.eq(i).find('input,select,textarea,label').each(function() {
                                updateElementIndex($(this), options.prefix, i);
                            });
                        }
                    }
                    // If a post-delete callback was provided, call it with the deleted form:
                    if (options.removed) options.removed(row);
                    return false;
                });
            };

        $$.each(function(i) {
            var row = $(this),
                del = row.find('input:checkbox[id $= "-DELETE"]');
            if (del.length) {
                // If you specify "can_delete = True" when creating an inline formset,
                // Django adds a checkbox to each form in the formset.
                // Replace the default checkbox with a hidden field:
                del.before('<input type="hidden" name="' + del.attr('name') +'" id="' + del.attr('id') +'" />');
                del.remove();
            }
            if (hasChildElements(row)) {
                insertDeleteLink(row);
                row.addClass(options.formCssClass);
                applyExtraClasses(row, i);
            }
        });

        if ($$.length) {
            var addButton, template;
            if (options.formTemplate) {
                // If a form template was specified, we'll clone it to generate new form instances:
                template = (options.formTemplate instanceof $) ? options.formTemplate : $(options.formTemplate);
                template.removeAttr('id').addClass(options.formCssClass).addClass('formset-custom-template');
                template.find('input,select,textarea,label').each(function() {
                    updateElementIndex($(this), options.prefix, 2012);
                });
                insertDeleteLink(template);
            } else {
                // Otherwise, use the last form in the formset; this works much better if you've got
                // extra (>= 1) forms (thnaks to justhamade for pointing this out):
                template = $('.' + options.formCssClass + ':last').clone(true).removeAttr('id');
                template.find('input:hidden[id $= "-DELETE"]').remove();
                template.find('input,select,textarea,label').each(function() {
                    var elem = $(this);
                    // If this is a checkbox or radiobutton, uncheck it.
                    // This fixes Issue 1, reported by Wilson.Andrew.J:
                    if (elem.is('input:checkbox') || elem.is('input:radio')) {
                        elem.attr('checked', false);
                    } 
                    /*else {
                        elem.val('');
                    }*/
                });
            }
            // FIXME: Perhaps using $.data would be a better idea?
            options.formTemplate = template;

            if ($$.attr('tagName') == 'TR') {
                // If forms are laid out as table rows, insert the
                // "add" button in a new table row:
                var numCols = $$.eq(0).children().length;
                $$.parent().append('<tr><td colspan="' + numCols + '"><a class="' + options.addCssClass + '" href="javascript:void(0)">' + options.addText + '</a></tr>');
                addButton = $$.parent().find('tr:last a');
                addButton.parents('tr').addClass(options.formCssClass + '-add');
            } else {
                // Otherwise, insert it immediately after the last form:
                $$.filter(':last').after('<a class="' + options.addCssClass + '" href="javascript:void(0)">' + options.addText + '</a>');
                addButton = $$.filter(':last').next();
            }
            addButton.click(function() {
                var formCount = parseInt($('#id_' + options.prefix + '-TOTAL_FORMS').val()),
                    row = options.formTemplate.clone(true).removeClass('formset-custom-template'),
                    buttonRow = $(this).parents('tr.' + options.formCssClass + '-add').get(0) || this;
                applyExtraClasses(row, formCount);
                row.insertBefore($(buttonRow)).show();
                row.find('input,select,textarea,label').each(function() {
                    updateElementIndex($(this), options.prefix, formCount);
                });
                $('#id_' + options.prefix + '-TOTAL_FORMS').val(formCount + 1);
                // If a post-add callback was supplied, call it with the added form:
                if (options.added) options.added(row);
                return false;
            });
        }

        return $$;
    }

    /* Setup plugin defaults */
    $.fn.formset.defaults = {
        prefix: 'form',                  // The form prefix for your django formset
        formTemplate: null,              // The jQuery selection cloned to generate new form instances
        addText: 'add another',          // Text for the add link
        deleteText: 'remove',            // Text for the delete link
        addCssClass: 'add-row',          // CSS class applied to the add link
        deleteCssClass: 'delete-row',    // CSS class applied to the delete link
        formCssClass: 'dynamic-form',    // CSS class applied to each form in a formset
        extraClasses: [],                // Additional CSS classes, which will be applied to each form in turn
        added: null,                     // Function called each time a new form is added
        removed: null                    // Function called each time a form is deleted
    };
})(jQuery);


/**
 * Сериализатор формы в объект
 * см. http://stackoverflow.com/questions/1184624/convert-form-data-to-js-object-with-jquery
 * а так же http://jsfiddle.net/sxGtM/3/
 *
 * @return {Object}
 */
$.fn.serializeObject = function() {
    var o = {};
    var a = this.serializeArray();
    $.each(a, function() {
        if (o[this.name] !== undefined) {
            if (!o[this.name].push) {
                o[this.name] = [o[this.name]];
            }
            o[this.name].push(this.value || '');
        } else {
            o[this.name] = this.value || '';
        }
    });
    return o;
};

/*
	Masked Input plugin for jQuery
	Copyright (c) 2007-@Year Josh Bush (digitalbush.com)
	Licensed under the MIT license (http://digitalbush.com/projects/masked-input-plugin/#license)
	Version: @version

	Fork: https://raw.github.com/kzap/jquery.maskedinput/master/src/jquery.maskedinput.js

	Callbacks:
		completed - Executes after the mask has been filled
		afterBlur - Executes after the value has changed and the blur has occurred
*/
(function($) {
	var pasteEventName = ($.browser.msie ? 'paste' : 'input') + ".mask";
	var iPhone = (window.orientation != undefined);

	$.mask = {
		//Predefined character definitions
		definitions: {
			'9': "[0-9]",
			'a': "[A-Za-zа-яА-Я]",
			'A': "[A-ZА-Я]",
			'*': "[A-Za-zа-яА-Я0-9]"
		},
		dataName:"rawMaskFn"
	};

	$.fn.extend({
		//Helper Function for Caret positioning
		caret: function(begin, end) {
			if (this.length == 0) return;
			if (typeof begin == 'number') {
				end = (typeof end == 'number') ? end : begin;
				return this.each(function() {
					if (this.setSelectionRange) {
						this.setSelectionRange(begin, end);
					} else if (this.createTextRange) {
						var range = this.createTextRange();
						range.collapse(true);
						range.moveEnd('character', end);
						range.moveStart('character', begin);
						range.select();
					}
				});
			} else {
				if (this[0].setSelectionRange) {
					begin = this[0].selectionStart;
					end = this[0].selectionEnd;
				} else if (document.selection && document.selection.createRange) {
					var range = document.selection.createRange();
					begin = 0 - range.duplicate().moveStart('character', -100000);
					end = begin + range.text.length;
				}
				return { begin: begin, end: end };
			}
		},
		unmask: function() { return this.trigger("unmask"); },
		mask: function(mask, settings) {
			if (!mask) {
				if(this.length > 0) {
					var fn = $(this).data($.mask.dataName);
					if($.isFunction(fn)) {
						return fn();
					};
				}
			return undefined;
			}
			settings = $.extend({
				placeholder: "_",
				completed: null,
				afterBlur: null
			}, settings);

			var defs = $.mask.definitions;
			var tests = [];
			var partialPosition = mask.length;
			var firstNonMaskPos = null;
			var len = mask.length;

			$.each(mask.split(""), function(i, c) {
				if (c == '?') {
					len--;
					partialPosition = i;
				} else if (defs[c]) {
					tests.push(new RegExp(defs[c]));
					if(firstNonMaskPos==null)
						firstNonMaskPos =  tests.length - 1;
				} else {
					tests.push(null);
				}
			});

			return this.trigger("unmask").each(function() {
				var input = $(this);
				var buffer = $.map(mask.split(""), function(c, i) { if (c != '?') return defs[c] ? settings.placeholder[i % settings.placeholder.length] : c });
				var focusText = input.val();

				function seekNext(pos) {
					while (++pos <= len && !tests[pos]);
					return pos;
				};
				function seekPrev(pos) {
					while (--pos >= 0 && !tests[pos]);
					return pos;
				};

				function shiftL(begin,end) {
					if(begin<0)
					   return;
					for (var i = begin,j = seekNext(end); i < len; i++) {
						if (tests[i]) {
							if (j < len && tests[i].test(buffer[j])) {
								buffer[i] = buffer[j];
								buffer[j] = settings.placeholder;
							} else
								break;
							j = seekNext(j);
						}
					}
					writeBuffer();
					input.caret(Math.max(firstNonMaskPos, begin));
				};

				function shiftR(pos) {
					for (var i = pos, c = settings.placeholder; i < len; i++) {
						if (tests[i]) {
							var j = seekNext(i);
							var t = buffer[i];
							buffer[i] = c;
							if (j < len && tests[j].test(t))
								c = t;
							else
								break;
						}
					}
				};

				function keydownEvent(e) {
					var k = e.which;

					//backspace, delete, and escape get special treatment
					if (k == 8 || k == 46 || (iPhone && k == 127)) {
						var pos = input.caret(),
							begin = pos.begin,
							end = pos.end;

						if (end-begin == 0) {
							begin = k != 46 ? seekPrev(begin) : (end = seekNext(begin-1));
							end = k == 46 ? seekNext(end) : end;
						}
						clearBuffer(begin, end);
						shiftL(begin, end-1);

						return false;
					} else if (k == 27) {//escape
						input.val(focusText);
						input.caret(0, checkVal());
						return false;
					}
				};

				function keypressEvent(e) {
					var k = e.which,
						pos = input.caret();
					if (e.ctrlKey || e.altKey || e.metaKey || k < 32) {//Ignore
						return true;
					} else if (k) {
						if(pos.end-pos.begin != 0) {
							clearBuffer(pos.begin, pos.end);
							shiftL(pos.begin, pos.end-1);
						}

						var p = seekNext(pos.begin - 1);
						if (p < len) {
							var c = String.fromCharCode(k);
							if (tests[p].test(c)) {
								shiftR(p);
								buffer[p] = c;
								writeBuffer();
								var next = seekNext(p);
								input.caret(next);
								if (settings.completed && next >= len)
									settings.completed.call(input);
							}
						}
						return false;
					}
				};

				function blurEvent(e) {
					checkVal();

					//if the value differs from original, triggers the change event
					if (input.val() != focusText) {
						input.change();
					}

					//if an afterBlur callback has been defined
					if(settings.afterBlur) {
						settings.afterBlur.call(input);
					}
				};

				function clearBuffer(start, end) {
					for (var i = start; i < end && i < len; i++) {
						if (tests[i])
							buffer[i] = settings.placeholder[i % settings.placeholder.length];
					}
				};

				function writeBuffer() { return input.val(buffer.join('')).val(); };

				function checkVal(allow) {
					//try to place characters where they belong
					var test = input.val(), lastMatch = -1;
					for (var i = 0, pos = 0; i < len; i++) {
						if (tests[i]) {
							buffer[i] = settings.placeholder[i % settings.placeholder.length];
							while (pos++ < test.length) {
								var c = test.charAt(pos - 1);
								if (tests[i].test(c)) {
									buffer[i] = c;
									lastMatch = i;
									break;
								}
							}
							if (pos > test.length)
								break;
						} else if (i!=partialPosition) {
							if(buffer[i] == test.charAt(pos)) {
								pos++;
								lastMatch = i;
							} else {
								lastMatch++;
							}
						}
					}
					if (!allow && lastMatch + 1 < partialPosition) {
						input.val("");
						clearBuffer(0, len);
					} else if (allow || lastMatch + 1 >= partialPosition) {
						writeBuffer();
						if (!allow) input.val(input.val().substring(0, lastMatch + 1));
					}
					return (partialPosition ? i : firstNonMaskPos);
				};

				input.data($.mask.dataName,function() {
					return $.map(buffer, function(c, i) {
						return tests[i]&&c!=settings.placeholder[i % settings.placeholder.length] ? c : null;
					}).join('');
				})

				if (!input.attr("readonly"))
					input
					.one("unmask", function() {
						input
							.unbind(".mask")
							.removeData($.mask.dataName);
					})
					.bind("focus.mask", function() {
						focusText = input.val();
						var pos = checkVal();
						writeBuffer();
						var moveCaret=function() {
							if (pos == mask.length)
								input.caret(0, pos);
							else
								input.caret(pos);
						};
						($.browser.msie ? moveCaret:function(){setTimeout(moveCaret,0)})();
					})
					.bind("blur.mask", blurEvent)
					.bind("keydown.mask", keydownEvent)
					.bind("keypress.mask", keypressEvent)
					.bind(pasteEventName, function() {
						setTimeout(function() { input.caret(checkVal(true)); }, 0);
					});

				checkVal(); //Perform initial check for existing values
			});
		},

		autoMask: function() {
			return $(this).on("focus", "input:text[data-mask]", function(e) {
				var $input = $(this),
					dataMask = $input.data("mask");

				if( dataMask !== undefined && $input.mask() === undefined ) {
					$input.mask(dataMask);
				}
			});
		}
	});
})(jQuery);

/**
 * jQuery.ScrollTo
 * Copyright (c) 2007-2009 Ariel Flesler - aflesler(at)gmail(dot)com | http://flesler.blogspot.com
 * Dual licensed under MIT and GPL.
 * Date: 5/25/2009
 *
 * @projectDescription Easy element scrolling using jQuery.
 * http://flesler.blogspot.com/2007/10/jqueryscrollto.html
 * Works with jQuery +1.2.6. Tested on FF 2/3, IE 6/7/8, Opera 9.5/6, Safari 3, Chrome 1 on WinXP.
 *
 * @author Ariel Flesler
 * @version 1.4.2
 *
 * @id jQuery.scrollTo
 * @id jQuery.fn.scrollTo
 * @param {String, Number, DOMElement, jQuery, Object} target Where to scroll the matched elements.
 *	  The different options for target are:
 *		- A number position (will be applied to all axes).
 *		- A string position ('44', '100px', '+=90', etc ) will be applied to all axes
 *		- A jQuery/DOM element ( logically, child of the element to scroll )
 *		- A string selector, that will be relative to the element to scroll ( 'li:eq(2)', etc )
 *		- A hash { top:x, left:y }, x and y can be any kind of number/string like above.
*		- A percentage of the container's dimension/s, for example: 50% to go to the middle.
 *		- The string 'max' for go-to-end.
 * @param {Number} duration The OVERALL length of the animation, this argument can be the settings object instead.
 * @param {Object,Function} settings Optional set of settings or the onAfter callback.
 *	 @option {String} axis Which axis must be scrolled, use 'x', 'y', 'xy' or 'yx'.
 *	 @option {Number} duration The OVERALL length of the animation.
 *	 @option {String} easing The easing method for the animation.
 *	 @option {Boolean} margin If true, the margin of the target element will be deducted from the final position.
 *	 @option {Object, Number} offset Add/deduct from the end position. One number for both axes or { top:x, left:y }.
 *	 @option {Object, Number} over Add/deduct the height/width multiplied by 'over', can be { top:x, left:y } when using both axes.
 *	 @option {Boolean} queue If true, and both axis are given, the 2nd axis will only be animated after the first one ends.
 *	 @option {Function} onAfter Function to be called after the scrolling ends.
 *	 @option {Function} onAfterFirst If queuing is activated, this function will be called after the first scrolling ends.
 * @return {jQuery} Returns the same jQuery object, for chaining.
 *
 * @desc Scroll to a fixed position
 * @example $('div').scrollTo( 340 );
 *
 * @desc Scroll relatively to the actual position
 * @example $('div').scrollTo( '+=340px', { axis:'y' } );
 *
 * @dec Scroll using a selector (relative to the scrolled element)
 * @example $('div').scrollTo( 'p.paragraph:eq(2)', 500, { easing:'swing', queue:true, axis:'xy' } );
 *
 * @ Scroll to a DOM element (same for jQuery object)
 * @example var second_child = document.getElementById('container').firstChild.nextSibling;
 *			$('#container').scrollTo( second_child, { duration:500, axis:'x', onAfter:function(){
 *				alert('scrolled!!');
 *			}});
 *
 * @desc Scroll on both axes, to different values
 * @example $('div').scrollTo( { top: 300, left:'+=200' }, { axis:'xy', offset:-20 } );
 */
;(function( $ ) {

	var $scrollTo = $.scrollTo = function( target, duration, settings ) {
		$(window).scrollTo( target, duration, settings );
	};

	$scrollTo.defaults = {
		axis:'xy',
		duration: parseFloat($.fn.jquery) >= 1.3 ? 0 : 1
	};

	// Returns the element that needs to be animated to scroll the window.
	// Kept for backwards compatibility (specially for localScroll & serialScroll)
	$scrollTo.window = function( scope ) {
		return $(window)._scrollable();
	};

	// Hack, hack, hack :)
	// Returns the real elements to scroll (supports window/iframes, documents and regular nodes)
	$.fn._scrollable = function() {
		return this.map(function() {
			var elem = this,
				isWin = !elem.nodeName || $.inArray( elem.nodeName.toLowerCase(), ['iframe','#document','html','body'] ) != -1;

				if ( !isWin )
					return elem;

			var doc = (elem.contentWindow || elem).document || elem.ownerDocument || elem;

			return $.browser.safari || doc.compatMode == 'BackCompat' ?
				doc.body :
				doc.documentElement;
		});
	};

	$.fn.scrollTo = function( target, duration, settings ) {
		if ( typeof duration == 'object' ) {
			settings = duration;
			duration = 0;
		}
		if ( typeof settings == 'function' )
			settings = { onAfter:settings };

		if ( target == 'max' )
			target = 9e9;

		settings = $.extend( {}, $scrollTo.defaults, settings );
		// Speed is still recognized for backwards compatibility
		duration = duration || settings.speed || settings.duration;
		// Make sure the settings are given right
		settings.queue = settings.queue && settings.axis.length > 1;

		if ( settings.queue )
			// Let's keep the overall duration
			duration /= 2;
		settings.offset = both( settings.offset );
		settings.over = both( settings.over );

		return this._scrollable().each(function() {
			var elem = this,
				$elem = $(elem),
				targ = target, toff, attr = {},
				win = $elem.is('html,body');

			switch( typeof targ ) {
				// A number will pass the regex
				case 'number':
				case 'string':
					if ( /^([+-]=)?\d+(\.\d+)?(px|%)?$/.test(targ) ) {
						targ = both( targ );
						// We are done
						break;
					}
					// Relative selector, no break!
					targ = $(targ,this);
				case 'object':
					// DOMElement / jQuery
					if ( targ.is || targ.style )
						// Get the real position of the target
						toff = (targ = $(targ)).offset();
			}
			$.each( settings.axis.split(''), function( i, axis ) {
				var Pos	= axis == 'x' ? 'Left' : 'Top',
					pos = Pos.toLowerCase(),
					key = 'scroll' + Pos,
					old = elem[key],
					max = $scrollTo.max(elem, axis);

				if ( toff ) {// jQuery / DOMElement
					attr[key] = toff[pos] + ( win ? 0 : old - $elem.offset()[pos] );

					// If it's a dom element, reduce the margin
					if ( settings.margin ) {
						attr[key] -= parseInt(targ.css('margin'+Pos)) || 0;
						attr[key] -= parseInt(targ.css('border'+Pos+'Width')) || 0;
					}

					attr[key] += settings.offset[pos] || 0;

					if ( settings.over[pos] )
						// Scroll to a fraction of its width/height
						attr[key] += targ[axis=='x'?'width':'height']() * settings.over[pos];
				} else {
					var val = targ[pos];
					// Handle percentage values
					attr[key] = val.slice && val.slice(-1) == '%' ?
						parseFloat(val) / 100 * max
						: val;
				}

				// Number or 'number'
				if ( /^\d+$/.test(attr[key]) )
					// Check the limits
					attr[key] = attr[key] <= 0 ? 0 : Math.min( attr[key], max );

				// Queueing axes
				if ( !i && settings.queue ) {
					// Don't waste time animating, if there's no need.
					if ( old != attr[key] )
						// Intermediate animation
						animate( settings.onAfterFirst );
					// Don't animate this axis again in the next iteration.
					delete attr[key];
				}
			});

			animate( settings.onAfter );

			function animate( callback ) {
				$elem.animate( attr, duration, settings.easing, callback && function() {
					callback.call(this, target, settings);
				});
			};

		}).end();
	};

	// Max scrolling position, works on quirks mode
	// It only fails (not too badly) on IE, quirks mode.
	$scrollTo.max = function( elem, axis ) {
		var Dim = axis == 'x' ? 'Width' : 'Height',
			scroll = 'scroll'+Dim;

		if ( !$(elem).is('html,body') )
			return elem[scroll] - $(elem)[Dim.toLowerCase()]();

		var size = 'client' + Dim,
			html = elem.ownerDocument.documentElement,
			body = elem.ownerDocument.body;

		return Math.max( html[scroll], body[scroll] )
			 - Math.min( html[size]  , body[size]   );

	};

	function both( val ) {
		return typeof val == 'object' ? val : { top:val, left:val };
	};

})( jQuery );

/*
    jQuery topLink Plugin

    http://davidwalsh.name/jquery-top-link
 */
jQuery.fn.topLink = function(settings) {
	settings = jQuery.extend({
		min: 1,
		fadeSpeed: 200,
		ieOffset: 50
	}, settings);
	return this.each(function() {
		//listen for scroll
		var el = $(this);
		el.css('display','none'); //in case the user forgot
		$(window).scroll(function() {
			if (!jQuery.support.hrefNormalized) {
				el.css({
					'position': 'absolute',
					'top': $(window).scrollTop() + $(window).height() - settings.ieOffset
				});
			}
			if ($(window).scrollTop() >= settings.min) {
				el.fadeIn(settings.fadeSpeed);
			} else {
				el.fadeOut(settings.fadeSpeed);
			}
		});
	});
};

jQuery.fn.filterOn = function(selector, values) {
    return this.each(function() {
        var select = this;
        //сохраняем все элементы
        var options = [];
        $(select).find('option').each(function() {
            options.push({value: $(this).val(), text: $(this).text()});
        });
        $(select).data('options', options);
        $(selector).change(function() {
            var selected = $(select).val();
            var options = $(select).empty().data('options');
            //список возможных значений для данного варианта
            var haystack = values[$(this).val()];
            $.each(options, function(i) {
                var option = options[i];
                //проверяем нужен ли элемент при данном варианте
                if ($.inArray(option.value, haystack) !== -1) {
                    var option_el = $('<option>').text(option.text).val(option.value);
                    //проверяем был ли выбран элемент
                    if ($.inArray(option.value, selected) !== -1) {
                        option_el.attr('selected', 'selected');
                    };
                    $(select).append(option_el);
                }
            });
            //необходимо для bsmselect
            $(select).trigger('change');
        });
    });
};
