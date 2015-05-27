// model function for kindergtn
function KinderGtn(data) {
  var self = this;
  this.display = ko.observable(true);
  this.status = ko.observable('initial');
  this.errMsg = ko.observable('');
  this.allowedStatus = ['initial', 'processing', 'ready'];

  this.id = ko.observable(data.id);
  this.shortName = ko.observable(data.short_name);
  this.ageGroupsIds = ko.observable(data.age_groups);
  this.sadikGroups = ko.observableArray();
  this.activeDistribution = ko.observable(data.active_distribution || false);

  this.addSadikGroup = function(data, ageGroups) {
    var sadikGroup = new SadikGroup(data, ageGroups);
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
    if (self.activeDistribution()) {
      return self.shortName();
    } else {
      return self.shortName() + ' - Этот ДОУ не принимает участия в респеделении';
    }
  }, this);

}

function AgeGroup(data) {
  this.id = ko.observable(data.id);
  this.name = ko.observable(data.name);
  this.shortName = ko.observable(data.short_name);
  this.minBirthDate = ko.observable(data.min_birth_date);
  this.maxBirthDate = ko.observable(data.max_birth_date);
}

function SadikGroup(data, ageGroups) {
  self = this;
  this.id = ko.observable(data.id || '');
  this.capacity = ko.observable(data.capacity || 0);
  this.freePlaces = ko.observable(data.free_places || 0);
  this.ageGroup = ko.observable(data.age_group);
  this.renderName = ko.observable();

  this.ageGroups = ageGroups;

  this.name = ko.pureComputed(function() {
    var ageGroupId = self.ageGroup();
    var ageGroup = ko.utils.arrayFirst(self.ageGroups(), function(item) {
      return item.id() === ageGroupId;
    });
    return ageGroup.name();
  }, this);
}


function KgListViewModel() {
  var self = this;
  this.KinderGtnList = ko.observableArray();
  this.filterText = ko.observable('');

  this.ageGroups = ko.observableArray();
  this.viewStatus = ko.observable();
  this.distributionIsActive = ko.observable(distribution_is_active);

  self.init = function() {
    this.viewStatus("Загружается список ДОУ и данные возрастных групп...");
    var kgxhr = self.loadKinderGtns();
    var agxhr = self.loadAgeGroups();
    $.when(kgxhr, agxhr).done(function() {self.viewStatus('');});
  }

  // selecting kindergartens to show on the page, filtering them
  this.kindergtnsToShow = ko.pureComputed(function() {
    var text = this.filterText().toLowerCase();
    if (text) {
      return ko.utils.arrayFilter(this.KinderGtnList(), function(kg) {
        return kg.shortName().toLowerCase().indexOf(text) > -1;
      });
    }
    return this.KinderGtnList();
  }, this);

  this.getSadikGroups = function(kg) {
    if (kg.isProcessing() || kg.isReady()) {
      return;
    }

    kg.setStatus('processing');
    $.getJSON('/api2/sadik/' + kg.id() + '/groups/', function(data) {
      $.each(kg.ageGroupsIds(), function(key, val) {
        // ищем подходящую группу среди полученных активных групп в садике
        sadikGroup = data.filter(function(item) {
          return item.age_group == val;
        });
        // если такая группа есть и она одна - используем её данные
        if (sadikGroup.length == 1) {
          kg.addSadikGroup(sadikGroup[0], self.ageGroups);
          // если таких групп несколько - ошибка, запрещаем работу с ДОУ
        } else if (sadikGroup.length > 1) {
          kg.display(false);
          kg.errMsg('Данный ДОУ содержит более одной активной группы для определенного возраста. Сообщите о проблеме в техническую поддержку.');
            // если такой группы нет - создаем новую
        } else {
          kg.addSadikGroup({'age_group': val}, self.ageGroups);
        }
      });
    }).error(function(e) {
      kg.display(false);
      kg.errMsg('Ошибка при попытке загрузить данные о доступных для зачисления группах. Обновите страницу и попробуйте еще раз');
      console.log('error while downloading sadikgroups list');
    }).always(function() {
      kg.setStatus('ready');
    });
  };

  // downloading json of kindergartens objects
  self.loadKinderGtns = function() {
    var xhr = $.getJSON('/api2/sadik/simple_info/', function(data) {
      $.each(data, function(key, val) {
        self.KinderGtnList.push(new KinderGtn(val));
      });
    }).error(function(e) {
      console.log('error while downloading kindergtns list');
    });
    return xhr;
  };

  self.loadAgeGroups = function() {
    // downloading json of agegroups objects
    var xhr = $.getJSON('/api2/age_groups/', function(data) {
      $.each(data, function(key, val) {
        self.ageGroups.push(new AgeGroup(val));
      });
    }).error(function(e) {
      console.log('error while downloading agegroups list');
    });
    return xhr;
  };
}

vm = new KgListViewModel();
ko.applyBindings(vm);

vm.init();

ko.bindingHandlers.highlightedText = {
  update: function(element, valueAccessor) {
    var options = valueAccessor();
    var value = ko.utils.unwrapObservable(options.text);
    var search = ko.utils.unwrapObservable(options.highlight);
    // remove previous highlight, if no filter value present
    if (search.length === 0) {
      element.innerHTML = value;
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
    }
  }
};

/** Binding to make content appear with 'fade' effect */
ko.bindingHandlers.fadeIn = {
    update: function(element, valueAccessor) {
        var options = valueAccessor();
        if(options() === true)
          $(element).hide().slideDown('slow');
          // $(element).fadeIn('slow');
    }
};
