#
# /etc/bash.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

PS1='[\u@\h \W]\$ '
PS2='> '
PS3='> '
PS4='+ '

case ${TERM} in
  xterm*|rxvt*|Eterm|aterm|kterm|gnome*)
    PROMPT_COMMAND=${PROMPT_COMMAND:+$PROMPT_COMMAND; }'printf "\033]0;%s@%s:%s\007" "${USER}" "${HOSTNAME%%.*}" "${PWD/#$HOME/\~}"'

    ;;
  screen)
    PROMPT_COMMAND=${PROMPT_COMMAND:+$PROMPT_COMMAND; }'printf "\033_%s@%s:%s\033\\" "${USER}" "${HOSTNAME%%.*}" "${PWD/#$HOME/\~}"'
    ;;
esac

[ -r /usr/share/bash-completion/bash_completion   ] && . /usr/share/bash-completion/bash_completion


##############

HISTSIZE=100000

alias vim='vim -p'
alias vi='vim -p'
alias less='less -R'

alias pip-pypy='/opt/pypy/bin/pip'
alias virtualenv-pypy='/opt/pypy/bin/virtualenv'
alias ipython-pypy='/opt/pypy/bin/ipython'

# ss/netstat
# listening, numeric, tcp, udp, processes
alias Ss='ss -lntup'

polipo_proxy () {
    export http_proxy='http://127.0.0.1:8123'
    export https_proxy=$http_proxy
    export HTTP_PROXY=$http_proxy
    export HTTPS_PROXY=$http_proxy
}
no_proxy () {
    unset http_proxy
    unset https_proxy
    unset HTTP_PROXY
    unset HTTPS_PROXY
}
#goagent_proxy () {
#    export http_proxy='http://127.0.0.1:8087'
#    export https_proxy=$http_proxy
#    export HTTP_PROXY=$http_proxy
#    export HTTPS_PROXY=$http_proxy
#}
#vps_proxy () {
#    export http_proxy='socks5://127.0.0.1:8088'
#    export https_proxy=$http_proxy
#    export HTTP_PROXY=$http_proxy
#    export HTTPS_PROXY=$http_proxy
#}
