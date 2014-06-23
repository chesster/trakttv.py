#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TraktTvPy

Usage:
  TraktTv.py search <term> [--add] [options]
  TraktTv.py watchlist [--delete] [--watch] [--unwatch] [options]

  TraktTv.py -h | --help
  TraktTv.py --version

Options:
 -d --details                   Detailed view
 -s --skip-watch-info           Skips informing you of watched episodes (HUGE timesaver)
 -l <limit> --limit=<limit>     Limit the output
 --todo                         Skips watched episodes in detailed view

"""
from __future__ import with_statement
import base64
import datetime
import hashlib
import json
import os
import sys
import types
import urllib2
from docopt import docopt
from clint.textui import puts, indent, colored
from clint.textui import progress as progress_bar


APIKEY   = ''
USER     = ''
PWD      = ''


class TraktTvAPI(object):

    GET_METHODS  = { 'activity/community', 'activity/episodes', 'activity/movies', 'activity/seasons', 'activity/shows', 'activity/user', 'activity/user/episodes', 'activity/user/movies', 'activity/user/seasons', 'activity/user/shows', 'calendar/premieres', 'calendar/shows', 'genres/movies', 'genres/shows', 'movie/comments', 'movie/related', 'movie/shouts', 'movie/stats', 'movie/summaries', 'movie/summary', 'movie/watchingnow', 'movies/trending', 'movies/updated', 'search/episodes', 'search/movies', 'search/people', 'search/shows', 'search/users', 'server/time', 'show/comments', 'show/episode/comments', 'show/episode/shouts', 'show/episode/stats', 'show/episode/summary', 'show/episode/watchingnow', 'show/related', 'show/season', 'show/seasons', 'show/shouts', 'show/stats', 'show/summaries', 'show/summary', 'show/watchingnow', 'shows/trending', 'shows/updated', 'user/calendar/shows', 'user/friends', 'user/lastactivity', 'user/library/movies/all', 'user/library/movies/collection', 'user/library/movies/hated', 'user/library/movies/loved', 'user/library/movies/watched', 'user/library/shows/all', 'user/library/shows/collection', 'user/library/shows/hated', 'user/library/shows/loved', 'user/library/shows/watched', 'user/list', 'user/lists', 'user/network/followers', 'user/network/following', 'user/network/friends', 'user/profile', 'user/progress/collected', 'user/progress/watched', 'user/ratings/episodes', 'user/ratings_movies', 'user/ratings/shows', 'user/watched', 'user/watched/episodes', 'user/watched/movies ' , 'user/watching', 'user/watchlist/episodes', 'user/watchlist/movies', 'user/watchlist/shows', }
    POST_METHODS = { 'movie/cancelcheckin', 'movie/cancelwatching', 'movie/checkin', 'movie/scrobble', 'movie/watching', 'show/cancelcheckin', 'show/cancelwatching', 'show/checkin', 'show/scrobble', 'show/watching', 'account/settings', 'account/test', 'activity/friends', 'comment/episode', 'comment/movie', 'comment/show', 'lists/add', 'lists/delete', 'lists/items/add', 'lists/items/delete', 'lists/update', 'movie/library', 'movie/seen', 'movie/unlibrary', 'movie/unseen', 'movie/unwatchlist', 'movie/watchlist', 'network/approve', 'network/deny', 'network/follow', 'network/requests', 'network/unfollow', 'rate/episode', 'rate/episodes', 'rate/movie', 'rate/movies', 'rate/show', 'rate/shows', 'recommendations/movies', 'recommendations/movies/dismiss', 'recommendations/shows', 'recommendations/shows/dismiss', 'show/episode/library', 'show/episode/seen', 'show/episode/unlibrary', 'show/episode/unseen', 'show/episode/unwatchlist', 'show/episode/watchlist', 'show/library', 'show/season/library', 'show/season/seen', 'show/seen', 'show/unlibrary', 'show/unwatchlist', 'show/watchlist', 'account/create' }

    @staticmethod
    def get_api(path):
        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(args[0], path, *args[1:], **kwargs)
            return wrapper
        return decorator


    def __init__(self, arg, user, pwd):

        self.api  = arg
        self.user = user
        self.pwd  = pwd

        def __post(args, post_data=None):
            path = ("https://api.trakt.tv/%s/%s/%s" % (args[0] + ('' if post_data else '.json'), self.api, "/".join([str(a) for a in args[1:]]))).rstrip('/')
            request = urllib2.Request(path)
            if post_data:
                post_data.update({"username": self.user, "password": hashlib.sha1(self.pwd).hexdigest(),})
                request.add_header('Content-Type', 'application/json')
            else:
                request.add_header("Authorization", "Basic %s" % base64.encodestring("%s:%s\n" % (self.user, self.pwd)))
            return json.load(urllib2.urlopen(request)) if not post_data else json.load(urllib2.urlopen(request, json.dumps(post_data)))

        for path in self.GET_METHODS:
            method_name = path.replace('/','_')
            @TraktTvAPI.get_api(path)
            def method(target, *args, **kwargs):
                return __post(args)
            setattr(self, "get_%s" % method_name, types.MethodType(method, self))

        for path in self.POST_METHODS:
            method_name = path.replace('/','_')
            @TraktTvAPI.get_api(path)
            def method(target, *args, **kwargs):
                return __post(args, kwargs)
            setattr(self, "post_%s" % method_name, types.MethodType(method, self))

    @staticmethod
    def _display_show(shows):
        return  [{'title': s['title'], 'id' : s['tvdb_id']} for s in shows]

    ##
    # API METHODS:
    ##
    def search(self, query, limit=10):
        return TraktTvAPI._display_show(self.get_search_shows(query, limit))

    def my_shows(self):
        return TraktTvAPI._display_show(self.get_user_watchlist_shows(self.user))

    def watched(self):
        return tv.get_user_library_shows_watched(self.user)


class TraktTvController(object):

    def __init__(self):
        self.arguments = docopt(__doc__, version='TraktTvPy 0.1')
        self.api = None
        self.auth()
        self.run()

    def run(self):
        for command in ('auth','search','watchlist',):
            if self.arguments.get(command, False) == True and hasattr(self, command):
                return getattr(self, command)()


    def auth(self):
        self.api = TraktTvAPI(APIKEY, USER, PWD)


    def search(self):
        results = self.api.search(self.arguments['<term>'], self.arguments['--limit'] or None)
        short_ids = self.__display_shows(results, self.arguments.get('--add', False))

        # ADD TO WATCHLIST
        if self.arguments.get('--add'):
            add_ids = raw_input('Enter Show IDs to add to watchlist (space separated): ').split(' ')
            self._add_shows_to_watchlist(*TraktTvController._short_id_to_tvdb_id(short_ids, add_ids))


    def watchlist(self):
        results = self.api.my_shows()
        limit = None if not self.arguments.get('--limit') else int(self.arguments.get('--limit'))
        show_short_ids = self.arguments.get('--delete', False) or self.arguments.get('--watch', False) or self.arguments.get('--unwatch', False)
        short_ids = self.__display_shows(results[:limit], show_short_ids)

        if self.arguments.get('--delete'):
            remove_ids = raw_input('Enter Show IDs to remove from watchlist (space separated): ').split(' ')
            self._remove_shows_from_watchlist(*TraktTvController._short_id_to_tvdb_id(short_ids, remove_ids))

        if self.arguments.get('--unwatch'):
            command = raw_input('Enter episodes you haven\'t watched (Ie: 2x3x10 2x3-3x3): ')
            self._watch_unwatch(command, short_ids, False)

        if self.arguments.get('--watch'):
            command = raw_input('Enter episodes you\'ve watched (Ie: 2x3x10 2x3-3x3): ')
            self._watch_unwatch(command, short_ids)


    def _watch_unwatch(self, command, short_ids, watch=True):
        commands = TraktTvController.__parse_command(command)
        if not command:
            return

        for command in progress_bar.bar(commands):
            show_id    = short_ids[command[0]]
            season_id  = command[1]
            episode_id = command[2]

            if season_id == -1 and episode_id == -1: # SHOW
                if watch:
                    self.api.post_show_seen(tvdb_id=show_id)
                else:
                    puts(colored.yellow('Cannot "unsee" a show - Skipping'))


            elif episode_id == -1: # SEASON
                if watch:
                    self.api.post_show_season_seen(tvdb_id=show_id, season=season_id)
                else:
                    puts(colored.yellow('Cannot "unsee" a season - Skipping'))

            else: # EPISODE
                if watch:
                    self.api.post_show_episode_seen(tvdb_id=show_id, episodes=[{'season':season_id, 'episode':episode_id}])
                else:
                    self.api.post_show_episode_unseen(tvdb_id=show_id, episodes=[{'season':season_id, 'episode':episode_id}])
            self.api.post_show_watchlist(shows=[{"tvdb_id": show_id},])


    def _add_shows_to_watchlist(self, *args):
        if 0 < len(args):
            shows_to_add = [{"tvdb_id": add_id} for add_id in args]
            add_result = self.api.post_show_watchlist(shows=shows_to_add)
            puts(colored.green('Shows added'))
        else:
            puts(colored.yellow('No shows added'))

    def _remove_shows_from_watchlist(self, *args):
        if 0 < len(args):
            shows_to_remove = [{"tvdb_id": add_id} for add_id in args]
            remove_result = self.api.post_show_unwatchlist(shows=shows_to_remove)
            puts(colored.green('Shows removed'))
        else:
            puts(colored.yellow('No shows removed'))

    @staticmethod
    def _short_id_to_tvdb_id(short_ids, ids):
        try:
            return [short_ids[int(i)] for i in ids]
        except ValueError, e:
            puts(colored.red("Operation Canceled"))
            return []

    @staticmethod
    def __pre_parse_command(command):
        a_list = []
        command = command.strip().split(" ")
        for comm in command:
            com_parts = comm.strip().split("x")
            el = []
            pos = 0
            append = True
            for p in com_parts:
                pos += 1
                ranges = p.split('-')
                if len(ranges) > 1:
                    rfrom = int(ranges[0])
                    rto = int(ranges[1])
                    for x in range(rfrom, rto+1):
                        eltmp = [e for e in el]
                        eltmp.append(int(x))
                        for n in range(1, 4-len(eltmp)):
                            eltmp.append(-1)
                        a_list.append(eltmp)
                    append = False
                else:
                    el.append(int(p))
            if append:
                for n in range(1, 4-len(el)):
                    el.append(-1)
                a_list.append(el)
        return a_list


    @staticmethod
    def __parse_command(command):
        try:
            return TraktTvController.__pre_parse_command(command)
        except ValueError:
            puts(colored.red("Invalid range syntax"))
            return None


    def __progress_to_episode_array(self, progress):
        episodes = {}
        for show in progress:
            show_id = show['show']['tvdb_id']
            if show_id and 0 < int(show_id):
                show_id = int(show_id)
                if not episodes.get(show_id):
                    episodes[show_id] = {}
                for s in show['seasons']:
                    season_id = int(s['season'])
                    for e in s['episodes'].keys():
                        if self.arguments.get('--todo'):
                            if not s['episodes'][e]:
                                if not episodes[show_id].get(season_id):
                                    episodes[show_id][season_id] = {}
                                episodes[show_id][season_id][int(e)] = s['episodes'][e]
                        else:
                            if not episodes[show_id].get(season_id):
                                episodes[show_id][season_id] = {}
                            episodes[show_id][season_id][int(e)] = s['episodes'][e]
        return episodes


    def __display_shows(self, shows, include_ids=False):

        id            = 0
        ids           = {}
        progress_dict = {}
        episode_dict  = {}
        skip_lookup   = False

        # GET WATCHED
        show_ids  = [s['id'] for s in shows]
        watchlist = ",".join([str(s) for s in show_ids])

        puts(colored.yellow('[Updating show Info]'))

        details = self.arguments.get('--details', False)

        if not (self.arguments.get('-s', False) or  self.arguments.get('--skip-watch-info', False)):
            progress = self.api.get_user_progress_watched(self.api.user, watchlist)
            for s in progress:
                if s['show']['tvdb_id'] and 0 < int(s['show']['tvdb_id']):
                    progress_dict[int(s['show']['tvdb_id'])] = int(s['progress']['left'])
            if details:
                episode_dict = self.__progress_to_episode_array(progress)

            # GET OTHER EPISODE INFO
            for show_id in progress_bar.bar(show_ids):
                if -1 == progress_dict.get(int(show_id), -1):
                    show_seasons = self.api.get_show_seasons(show_id)
                    total_episodes = sum([int(s['episodes']) for s in show_seasons])
                    progress_dict[int(show_id)] = int(total_episodes)
                    if details:
                        if not episode_dict.get(show_id):
                            episode_dict[int(show_id)] = {}
                        for season in show_seasons:
                            for episode in range(1,int(season['episodes'])+1):
                                sk = int(season['season'])
                                if not episode_dict[int(show_id)].get(sk):
                                    episode_dict[int(show_id)][sk] = {}
                                episode_dict[int(show_id)][sk][int(episode)] = False
        else:
            skip_lookup=True


        def watched(unwatched_episodes, f='[{n:1}]'):
            if not unwatched_episodes:
                return colored.green('[ok]')
            else:
                return colored.red(f.format(n=unwatched_episodes))

        # SHOW
        puts(colored.yellow('\n[Shows]'))
        format_str = "[{n:%s}]" % str(len(str(len(shows))))
        format_unwatched_episodes = "[{n:%s}]" % str(len(str(max([progress_dict[i] for i in progress_dict]))))
        for show in shows:
            unwatched_episodes = progress_dict.get(int(show['id']), 0)
            if (unwatched_episodes and self.arguments.get('--todo')) or not self.arguments.get('--todo'):
                w = colored.yellow('[skip]') if skip_lookup else watched(unwatched_episodes, format_unwatched_episodes)
                if include_ids:
                    id += 1
                    ids[id] = int(show['id'])
                    puts("%s %s %s" % (
                        w,
                        colored.yellow(format_str.format(n=id)),
                        show['title'].encode('utf8'),
                    ))
                else:
                    puts("%s %s" % (
                        w,
                        show['title'].encode('utf8'),
                    ))

                # DISPLAY SEASONS
                if self.arguments.get('--details', False) or self.arguments.get('-d', False):
                    with indent(2, quote='|'):
                        show_id = int(show['id'])
                        for _season in episode_dict[show_id].keys():
                            puts('Season %s' % _season)
                            with indent(1, quote='|'):
                                txt = ''
                                i = 0
                                for _episode in sorted(episode_dict[show_id][_season].keys()):
                                    i += 1
                                    txt = txt + ' '
                                    if episode_dict[show_id][_season][_episode]:
                                        txt = txt + colored.green('[%02dx%02d]' % (_season, _episode))
                                    else:
                                        txt = txt + colored.red('[%02dx%02d]' % (_season, _episode))

                                    if not divmod(i,7)[1]:
                                        puts(txt)
                                        txt = ''
                                if len(txt):
                                    puts(txt)
        return ids


if __name__ == '__main__':
    try:
        controller = TraktTvController()
    except EOFError, KeyboardInterrupt:
        puts(colored.red("\n[Exiting]"))
    except urllib2.URLError:
        puts("No Internet connection available " + colored.red("[Exiting]"))
