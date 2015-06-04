(function() {
  function KinderGtn(data) {
    var self = this;
    this.display = ko.observable(false);
    this.status = ko.observable('initial');
    this.disabled = ko.observable(false);
    this.messages = ko.observableArray();
    this.allowedStatus = ['initial', 'processing', 'ready'];

    this.id = data.id;
    this.shortName = data.short_name;
    this.ageGroupsIds = ko.observable(data.age_groups);
    this.sadikGroups = ko.observableArray();
    this.activeDistribution = data.active_distribution || false;

    this.addSadikGroup = function(data) {
      var sadikGroup = new SadikGroup(data);
      this.sadikGroups.push(sadikGroup);
      return sadikGroup;
    };

    this.setStatus = function(status) {
      if (self.allowedStatus.indexOf(status) > -1) {
        self.status(status);
      }
    };

    this.isInitial = ko.pureComputed(function() {
      return self.status() == 'initial';
    }, this);

    this.isProcessing = ko.pureComputed(function() {
      return self.status() == 'processing';
    }, this);

    this.isReady = ko.pureComputed(function() {
      return self.status() == 'ready';
    }, this);

    this.fullName = ko.pureComputed(function() {
      if (self.activeDistribution) {
        return self.shortName;
      } else {
        return self.shortName + ' - Этот ДОУ не принимает участия в распределении';
      }
    }, this);

  }

  function AgeGroup(data) {
    this.id = data.id;
    this.name = data.name;
    this.shortName = data.short_name;
    this.minBirthDate = data.min_birth_date;
    this.maxBirthDate = data.max_birth_date;
  }

  function SadikGroup(data) {
    self = this;
    this.id = data.id || null;
    this.capacity = ko.observable(data.capacity || 0).extend({
      trackChange: true, zeroInt: true});
    this.freePlaces = ko.observable(data.free_places || 0);
    this.ageGroupId = data.age_group;
    this.name = ko.observable();

    this.setName = function(ageGroups, year) {
      var ageGroup = ko.utils.arrayFirst(ageGroups(), function(item) {
        return item.id === self.ageGroupId;
      });
      self.name(ageGroup.name + ' за ' + current_distribution_year + ' год' + ' (c ' +
                ageGroup.minBirthDate + ' по ' + ageGroup.maxBirthDate + ')');
    };
  }

  function Message(data) {
    this.msgClass = ko.observable(data.class || 'alert');
    this.message = ko.observable(data.message || '');
  }

  function KgListViewModel() {
    var self = this;
    this.KinderGtnList = ko.observableArray();
    this.totalFreePlaces = ko.observable();
    this.totalCapacity = ko.observable();
    this.ageGroups = ko.observableArray();

    this.distributionIsActive = ko.observable(distribution_is_active);

    this.viewStatus = ko.observable();
    this.filterText = ko.observable('');
    this.activeKinderGtn = null;

    this.kgListCollapsed = ko.observable(true);
    this.collapseButtonText = ko.observable('Развернуть все');

    self.init = function() {
      self.viewStatus("Загружается список возрастных групп...");
      var agxhr = self.loadAgeGroups();
      $.when(agxhr).done(function() {
        self.viewStatus("Загружается список ДОУ...");
        var kgxhr = self.loadKinderGtns();
        $.when(kgxhr).done(function(){self.viewStatus('');});
      });

      self.loadPlaces();
    };

    this.toggleCollapseStatus = function () {
      self.kgListCollapsed(!self.kgListCollapsed());
      self.kgListCollapsed() ? self.collapseButtonText('Развернуть все') : self.collapseButtonText('Свернуть все');
    };

    this.showMessage = function(elem) {
      if (elem.nodeType === 1) {
        $(elem).hide().slideDown();
      }
    };

    this.addGroupsToKindergtn = function(kg, data) {
      /* Add groups to kindergtn according to it's array of allowed age groups.
       * First - lookup for proper group data object in passed data array.
       * If no group data for given age group foud, group generated
       * automatically, with default values.
       */

      var errFlag = false;
      $.each(kg.ageGroupsIds(), function(key, val) {
        // ищем подходящую группу среди активных возрастных групп в садике
        sadikGroup = data.filter(function(item) {
          return item.age_group == val;
        });
        // если такая группа есть и она одна - используем её данные
        var sg;
        if (sadikGroup.length == 1) {
          sg = kg.addSadikGroup(sadikGroup[0]);
          sg.setName(self.ageGroups);
        // если таких групп несколько - ошибка, запрещаем работу с ДОУ
        } else if (sadikGroup.length > 1) {
          errFlag = true;
          kg.sadikGroups.removeAll();
          kg.messages.removeAll();
          kg.messages.push(new Message({
            'class': 'alert',
            'message': 'Данный ДОУ содержит более одной активной группы для ' +
            'определенного возраста. Сообщите о проблеме в техническую поддержку.'
          }));
          return false;
        // если такой группы нет - создаем новую
        } else {
          sg = kg.addSadikGroup({'age_group': val}, self.ageGroups);
          sg.setName(self.ageGroups);
        }
      });

      kg.display(!errFlag);
    };

    this.getSadikGroups = function(kg) {
      if (kg.isProcessing() || self.activeKinderGtn == kg) {
        return;
      }

      if (!self.kgListCollapsed()) {
       self.toggleCollapseStatus();
      }

      kg.setStatus('processing');
      self.activeKinderGtn = kg;

      $.getJSON('/api2/sadik/' + kg.id + '/groups/', function(data) {
        kg.sadikGroups.removeAll();
        self.addGroupsToKindergtn(kg, data);
      }).error(function(e) {
        kg.display(false);
        kg.messages.push(new Message({
          'class': 'alert',
          'message': 'Ошибка при попытке загрузить данные о доступных для ' +
                     'зачисления группах. Обновите страницу и попробуйте еще раз'
        }));
        console.log('error while downloading sadikgroups list');
      }).always(function() {
        kg.setStatus('ready');
      });
    };

    this.saveSadikGroups = function(kg) {
      if (kg.disabled()) {
        return;
      }
      // chek if data changed
      var rawData = kg.sadikGroups().filter(function(item){return item.capacity.isChanged(); });
      var invalidData = kg.sadikGroups().filter(function(item){return !item.capacity.isValid(); });

      if (invalidData.length) {
        kg.messages.push(new Message({'class': 'alert', 'message': 'Исправьте ошибки заполнения данных'}));
      } else if (rawData.length) {
        kg.disabled(true);
        var data = ko.toJSON(rawData);
        $.post('/api2/sadik/' + kg.id + '/groups/', data, function(returnedData) {
          kg.sadikGroups.removeAll();
          self.addGroupsToKindergtn(kg, returnedData);
          kg.messages.push(new Message({'class': 'alert-success', 'message': 'Данные успешно сохранены'}));
        }).error(function() {
          kg.messages.push(new Message({'class': 'alert-danger', 'message': 'Ошибка во время сохранения данных'}));
        }).always(function() {
          self.loadPlaces();
          kg.disabled(false);
        });
      } else {
        kg.messages.push(new Message({'class': 'alert-info', 'message': 'Данные не изменялись'}));
      }
    };

    // downloading json of kindergartens objects
    self.loadKinderGtns = function() {
      var xhr = $.getJSON('/api2/sadik/simple_info/', function(data) {
        $.each(data, function(key, val) {
          var kg = new KinderGtn(val);
          self.KinderGtnList.push(kg);
          if (val.groups.length) {
            self.addGroupsToKindergtn(kg, val.groups.filter(function(group) {return group.active; }));
          }
        });
      }).error(function(e) {
        console.log('error while downloading kindergtns list');
      });
      return xhr;
    };

    // downloading json of agegroups objects
    self.loadAgeGroups = function() {
      var xhr = $.getJSON('/api2/age_groups/', function(data) {
        $.each(data, function(key, val) {
          self.ageGroups.push(new AgeGroup(val));
        });
      }).error(function(e) {
        console.log('error while downloading agegroups list');
      });
      return xhr;
    };

    // downloading json of places to kindergartens
    self.loadPlaces = function() {
      var xhr = $.getJSON('/api2/distributions/places/total/', function(data) {
        self.totalCapacity(data.total_capacity);
        self.totalFreePlaces(data.total_free_places);
      }).error(function(e) {
        console.log('error while downloading places info');
      });
      return xhr;

    };
  }

  vm = new KgListViewModel();
  ko.applyBindings(vm);

  vm.init();
})();

ko.validation.rules['zeroInt'] = {
  validator: function (val, validate) {
        return validate && /^([0-9]\d*)*$/.test(val.toString());
    },
    message: 'Укажите целое число больше нуля'
};
ko.validation.registerExtenders();
ko.validation.init({
  'errorClass': 'error',
  'decorateInputElement': true,
}, true);

ko.bindingHandlers.highlightHideText = {
  update: function(element, valueAccessor) {
    var options = valueAccessor();
    var value = ko.utils.unwrapObservable(options.text);
    var search = ko.utils.unwrapObservable(options.highlight);
    // remove previous highlight, if no filter value present
    if (search.length === 0) {
      element.innerHTML = value;
      $(element).parent().parent().show();
      return;
    }
    // could do this or something similar to escape HTML before replacement,
    // if there is a risk of HTML injection in this value
    if (options.sanitize) {
      value = $('<div/>').text(value).html();
    }
    var re = new RegExp(search, 'ig');
    // if found matches - highlighting them
    var match = value.match(re);
    if (match) {
      var replacement = '<span class="highlight">' + match[0] + '</span>';
      element.innerHTML = value.replace(re, replacement);
      $(element).parent().parent().show();
    } else {
      $(element).parent().parent().hide();
    }
  }
};

/** Binding to make content appear with 'slide' effect */
ko.bindingHandlers.slideOn = {
    update: function(element, valueAccessor) {
        var options = valueAccessor();
        if(options() === true) {
          $(element).hide().slideDown('slow');
        } else {
          $(element).hide();
        }
    }
};

ko.bindingHandlers.toggleCollapse = {
  update: function(element, valueAccessor) {
    var valueUnwrapped = ko.unwrap(valueAccessor());
    var $element = $(element);
    if (valueUnwrapped) {
      if ($element.hasClass('in')) {
        $element.removeClass('in');
        $element.css('height', '0');
      }
    } else {
      if (!$element.hasClass('in')) {
        $element.addClass('in');
        $element.css('height', 'auto');
      }
    }
  }
};


ko.extenders.trackChange = function (target, track) {
    if (track) {
        target.isChanged = ko.observable(false);
        target.originalValue = target();
        target.subscribe(function (newValue) {
            // use != not !== so numbers will equate naturally
            target.isChanged(newValue != target.originalValue);
        });
    }
    return target;
};
